import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import system_info  # noqa: E402


def put(root, path, text):
    target = os.path.join(root, path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as stream:
        stream.write(text)


class TelemetrySamplerTest(unittest.TestCase):
    def test_interval_rates_for_disk_and_network(self):
        with tempfile.TemporaryDirectory() as root:
            put(root, "proc/diskstats", "8 0 sda 10 0 20 0 30 0 40 0 0 0 0\n")
            put(root, "proc/net/dev", "Inter-| Receive | Transmit\neth0: 100 0 0 0 0 0 0 0 200 0 0 0 0 0 0 0\n")
            put(root, "sys/class/drm/card0/device/gpu_busy_percent", "44\n")
            clock = iter((0.0, 2.0)).__next__
            sampler = system_info.TelemetrySampler(os.path.join(root, "proc"), os.path.join(root, "sys"), clock)
            sampler.read()
            put(root, "proc/diskstats", "8 0 sda 10 0 30 0 30 0 60 0 0 0 0\n")
            put(root, "proc/net/dev", "Inter-| Receive | Transmit\neth0: 300 0 0 0 0 0 0 0 600 0 0 0 0 0 0 0\n")
            current = sampler.read()
            self.assertEqual(current["disks"][0]["read_bytes_sec"], 2560.0)
            self.assertEqual(current["disks"][0]["write_bytes_sec"], 5120.0)
            self.assertEqual(current["network"][0]["receive_bytes_sec"], 100.0)
            self.assertEqual(current["network"][0]["send_bytes_sec"], 200.0)
            self.assertEqual(current["gpu"][0]["busy_percent"], 44.0)


if __name__ == "__main__":
    unittest.main()
