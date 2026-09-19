import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import favorites, volumes  # noqa: E402


class FavoritesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = favorites.CONFIG_DIR
        favorites.CONFIG_DIR = self._tmp.name

    def tearDown(self):
        favorites.CONFIG_DIR = self._old
        self._tmp.cleanup()

    def test_roundtrip_with_odd_names(self):
        odd = ['/home/u/Dokumenty', '/mnt/a "b" c', "/mnt/čučoriedky\\x", "/srv/tab\there"]
        for path in odd:
            favorites.add(path)
        self.assertEqual(favorites.load(), odd)

    def test_add_is_idempotent_and_remove_works(self):
        favorites.add("/a")
        favorites.add("/a")
        favorites.add("/b")
        self.assertEqual(favorites.load(), ["/a", "/b"])
        self.assertEqual(favorites.remove("/a"), ["/b"])
        self.assertEqual(favorites.load(), ["/b"])

    def test_missing_and_broken_file(self):
        self.assertEqual(favorites.load(), [])
        with open(os.path.join(self._tmp.name, "favorites.toml"), "w") as f:
            f.write("[[favorite\npath = ")
        self.assertEqual(favorites.load(), [])

    def test_ignores_relative_paths(self):
        with open(os.path.join(self._tmp.name, "favorites.toml"), "w") as f:
            f.write('[[favorite]]\npath = "relative"\n[[favorite]]\npath = "/ok"\n')
        self.assertEqual(favorites.load(), ["/ok"])


class LocateTest(unittest.TestCase):
    def setUp(self):
        self._entries = volumes.SYSTEM_ENTRIES
        volumes.SYSTEM_ENTRIES = [("Users", "/"), ("Shared", "/srv")]
        self.tmp = tempfile.TemporaryDirectory()
        volumes.SYSTEM_ENTRIES = [("Users", self.tmp.name + "/home"), ("Shared", self.tmp.name + "/srv")]
        for _n, p in volumes.SYSTEM_ENTRIES:
            os.makedirs(p)
        self.system = volumes.Volume("System", "/", role="system")
        self.usb = volumes.Volume("Device2", "/run/media/u/USB", removable=True)
        self.vols = [self.system, self.usb]

    def tearDown(self):
        volumes.SYSTEM_ENTRIES = self._entries
        self.tmp.cleanup()

    def test_data_volume_root_is_volume_path(self):
        self.assertEqual(volumes.locate(self.vols, "/run/media/u/USB/foto/2024"), (self.usb, self.usb.path))

    def test_system_volume_only_allows_shown_entries(self):
        home = self.tmp.name + "/home"
        self.assertEqual(volumes.locate(self.vols, home + "/u/dev"), (self.system, home))
        self.assertIsNone(volumes.locate(self.vols, "/etc"))

    def test_unmounted_volume_never_matches(self):
        gone = volumes.Volume("Device3", None, removable=True, device="/dev/sdc1")
        self.assertIsNone(volumes.locate([gone], "/anything"))

    def test_volume_identity_survives_remount(self):
        before = volumes.Volume("Device2", None, device="/dev/sdb1", removable=True)
        after = volumes.Volume("Device2", "/run/media/u/X", device="/dev/sdb1", removable=True)
        self.assertEqual(before, after)
        self.assertIn(before, [after])


if __name__ == "__main__":
    unittest.main()
