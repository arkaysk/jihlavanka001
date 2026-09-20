import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import hardware_catalog, processes  # noqa: E402


def put(root, path, text):
    target = os.path.join(root, path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as stream:
        stream.write(text)


class ProcessBackendTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        put(self.root, "stat", "cpu 100 0 100 800 0 0 0 0 0 0\n")
        put(self.root, "meminfo", "MemTotal: 1024 kB\nMemAvailable: 256 kB\nSwapTotal: 512 kB\nSwapFree: 128 kB\n")
        put(self.root, "uptime", "42.5 0.0\n")
        put(self.root, "loadavg", "0.50 0.25 0.10 1/2 10\n")
        put(self.root, "123/stat", "123 (test worker) R 1 0 0 0 0 0 0 0 0 0 20 5 0 0 0 0 1 0 77 0\n")
        put(self.root, "123/status", "Uid:\t1000\t1000\t1000\t1000\nVmRSS:\t64 kB\n")
        put(self.root, "123/cmdline", "/usr/bin/test-worker\0--demo\0")
        put(self.root, "1/stat", "1 (init) S 0 0 0 0 0 0 0 0 0 0 1 1 0 0 0 0 1 0 11 0\n")
        put(self.root, "1/status", "Uid:\t0\t0\t0\t0\nVmRSS:\t128 kB\n")
        self.home = os.path.join(self.root, "home")
        put(self.home, ".config/autostart/demo.desktop", "[Desktop Entry]\nType=Application\nName=Demo\nExec=demo\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_processes_are_classified_and_parsed(self):
        found = processes.read_processes(self.root, current_uid=1000)
        by_pid = {item.pid: item for item in found}
        self.assertEqual(by_pid[123].kind, "user")
        self.assertEqual(by_pid[123].name, "test worker")
        self.assertEqual(by_pid[123].command, "/usr/bin/test-worker --demo")
        self.assertEqual(by_pid[123].cpu_ticks, 20)
        self.assertEqual(by_pid[1].kind, "system")

    def test_snapshot_reads_memory_uptime_and_load(self):
        snapshot = processes.Sampler(self.root, cpu_count=1).read()
        self.assertEqual(snapshot.memory_total, 1024 * 1024)
        self.assertEqual(snapshot.memory_used, 768 * 1024)
        self.assertEqual(snapshot.uptime, 42.5)
        self.assertEqual(snapshot.load, (0.5, 0.25, 0.1))

    def test_user_desktop_autorun_can_be_disabled(self):
        entries = processes.autorun_entries(self.home, os.path.join(self.root, "etc/xdg/autostart"))
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0].writable)
        processes.set_desktop_autorun(entries[0], False)
        with open(entries[0].source, encoding="utf-8") as stream:
            self.assertIn("Hidden=true", stream.read())


class HardwareCatalogTest(unittest.TestCase):
    def test_local_pci_catalog_is_offline_and_resolves_ids(self):
        with tempfile.TemporaryDirectory() as root:
            put(root, "hardware/pci.ids", "9abc  Test Vendor\n\t1234  Test Graphics\n")
            catalog = hardware_catalog.load(root)
            self.assertTrue(catalog.loaded)
            self.assertEqual(catalog.identify("9abc", "1234"), "Test Vendor Test Graphics")
            self.assertTrue(hardware_catalog.update_sources()["offline"])


if __name__ == "__main__":
    unittest.main()
