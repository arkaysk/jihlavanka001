import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import devices, volumes  # noqa: E402


def dev(kind, state, node="", **kw):
    return devices.Device(key=kw.pop("key", node or kind), kind=kind, state=state, node=node, **kw)


class ListVolumesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = (volumes.CONFIG_DIR, volumes.CONFIG_FILE, devices.detect, volumes._known_volumes)
        volumes.CONFIG_DIR = self._tmp.name
        volumes.CONFIG_FILE = os.path.join(self._tmp.name, "volumes.toml")
        self.found = []
        devices.detect = lambda: self.found

    def tearDown(self):
        volumes.CONFIG_DIR, volumes.CONFIG_FILE, devices.detect, volumes._known_volumes = self._old
        self._tmp.cleanup()

    def sample(self):
        return [
            dev("system", "mounted", "/dev/mapper/root", uuid="u-root", mountpoint="/", size=16 * 10**9),
            dev("usb", "no-fs", "/dev/sdb", removable=True, size=150 * 10**6),
            dev("optical", "unmounted", "/dev/sr0", uuid="cd-1", label="DISC", removable=True, size=50 * 10**6),
            dev("share", "mounted", key="share:vboxsf:Projekt", mountpoint="/media/sf_Projekt", share_name="Projekt",
                fstype="vboxsf"),
        ]

    def test_names_kinds_and_states(self):
        self.found = self.sample()
        vols = volumes.list_volumes()
        self.assertEqual([v.name for v in vols], ["Device1", "Device2", "Device3", "Projekt"])
        self.assertEqual([v.kind for v in vols], ["system", "usb", "optical", "share"])
        self.assertEqual([v.role for v in vols], ["system", "data", "data", "data"])
        self.assertEqual([v.mounted for v in vols], [True, False, False, True])
        self.assertEqual([v.mountable for v in vols], [False, False, True, False])
        self.assertIn("nemá súborový systém", vols[1].help_text)
        self.assertEqual(vols[3].fstype, "vboxsf")
        self.assertEqual(vols[2].kind_text, "Optická mechanika")

    def test_share_and_fixed_names_persist_but_removable_do_not(self):
        self.found = self.sample()
        vols = volumes.list_volumes()
        volumes.rename(vols[3], "Zdielane z hosta")
        volumes.rename(vols[0], "System")
        volumes.rename(vols[2], "Moje CD")
        again = volumes.list_volumes()
        self.assertEqual(again[0].name, "System")
        self.assertEqual(again[3].name, "Zdielane z hosta")
        self.assertNotEqual(again[2].name, "Moje CD")          # výmenné médium sa nepamätá

    def test_failure_keeps_last_known_list_and_reports_why(self):
        self.found = self.sample()
        good = volumes.list_volumes()

        def broken():
            raise RuntimeError("lsblk zlyhal: chýba")

        devices.detect = broken
        again = volumes.list_volumes()
        self.assertEqual([v.name for v in again], [v.name for v in good])
        self.assertIn("lsblk zlyhal", volumes.problem)
        devices.detect = lambda: self.found
        volumes.list_volumes()
        self.assertEqual(volumes.problem, "")

    def test_state_never_pretends_a_missing_device_is_usable(self):
        self.found = [dev("floppy", "no-driver", key="floppy:controller", removable=True)]
        floppy = volumes.list_volumes()[0]
        self.assertFalse(floppy.mounted or floppy.mountable)
        self.assertIn("ovládač", floppy.help_text)


if __name__ == "__main__":
    unittest.main()
