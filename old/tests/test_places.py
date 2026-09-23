import os
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import places  # noqa: E402


class PlacesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.users = os.path.join(self._tmp.name, "home")
        self.home = os.path.join(self.users, "kenshi")
        os.makedirs(self.home)
        self._env = {k: os.environ.get(k) for k in ("HOME", "XDG_DATA_HOME")}
        os.environ["HOME"] = self.home
        os.environ.pop("XDG_DATA_HOME", None)
        self.trash = os.path.join(self.home, ".local", "share", "Trash", "files")

    def tearDown(self):
        for key, value in self._env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self._tmp.cleanup()

    def test_trash_lives_in_the_users_own_home(self):
        self.assertEqual(places.trash_files(), self.trash)
        os.environ["HOME"] = os.path.join(self.users, "arkay")
        self.assertEqual(places.trash_files(), os.path.join(self.users, "arkay", ".local", "share", "Trash", "files"))

    def test_xdg_data_home_is_respected(self):
        os.environ["XDG_DATA_HOME"] = os.path.join(self.home, "data")
        self.assertEqual(places.trash_files(), os.path.join(self.home, "data", "Trash", "files"))

    def test_ensure_creates_files_and_info_private_to_the_user(self):
        self.assertIsNone(places.ensure_trash())
        self.assertTrue(os.path.isdir(self.trash))
        self.assertTrue(os.path.isdir(os.path.join(places.trash_root(), "info")))
        self.assertEqual(stat.S_IMODE(os.stat(places.trash_root()).st_mode), 0o700)
        self.assertIsNone(places.ensure_trash())            # opakované volanie nič nepokazí

    def test_ensure_reports_a_failure_instead_of_hiding_it(self):
        os.makedirs(os.path.join(self.home, ".local"))
        with open(os.path.join(self.home, ".local", "share"), "w") as f:      # súbor tam, kde má byť priečinok
            f.write("x")
        self.assertIn("Kôš", places.ensure_trash())

    def test_technical_path_collapses_into_one_folder(self):
        os.makedirs(os.path.join(self.trash, "stary-priecinok"))
        got = places.parts(self.users, os.path.join(self.trash, "stary-priecinok"))
        self.assertEqual(got, [("kenshi", self.home), ("Kôš", self.trash),
                               ("stary-priecinok", os.path.join(self.trash, "stary-priecinok"))])

    def test_trash_itself_and_home(self):
        self.assertEqual(places.parts(self.users, self.trash), [("kenshi", self.home), ("Kôš", self.trash)])
        self.assertEqual(places.parts(self.users, self.home), [("kenshi", self.home)])
        self.assertEqual(places.parts(self.home, self.home), [])

    def test_other_paths_are_untouched(self):
        docs = os.path.join(self.home, "Documents", "faktury")
        self.assertEqual([n for n, _p in places.parts(self.users, docs)], ["kenshi", "Documents", "faktury"])
        # ani iná časť ~/.local sa nezloží, len skutočný Kôš
        cache = os.path.join(self.home, ".local", "share", "applications")
        self.assertEqual([n for n, _p in places.parts(self.users, cache)], ["kenshi", ".local", "share", "applications"])

    def test_someone_elses_trash_is_not_shown_as_mine(self):
        other = os.path.join(self.users, "arkay", ".local", "share", "Trash", "files")
        self.assertEqual([n for n, _p in places.parts(self.users, other)],
                         ["arkay", ".local", "share", "Trash", "files"])

    def test_title_and_parent(self):
        self.assertEqual(places.title(self.trash), "Kôš")
        self.assertEqual(places.title(os.path.join(self.trash, "a.txt")), "a.txt")
        self.assertEqual(places.parent(self.trash), self.home)                      # Kôš je zložka v domove
        self.assertEqual(places.parent(os.path.join(self.trash, "a.txt")), self.trash)
        self.assertEqual(places.parent(os.path.join(self.home, "Documents")), self.home)

    def test_count(self):
        places.ensure_trash()
        self.assertEqual(places.count_trashed(), 0)
        open(os.path.join(self.trash, "a"), "w").close()
        self.assertEqual(places.count_trashed(), 1)
        self.assertEqual(places.count_trashed("/nie/je/tu"), 0)

    def test_in_trash(self):
        self.assertTrue(places.in_trash(self.trash))
        self.assertTrue(places.in_trash(os.path.join(self.trash, "x")))
        self.assertFalse(places.in_trash(self.trash + "-nie"))
        self.assertFalse(places.in_trash(self.home))


if __name__ == "__main__":
    unittest.main()
