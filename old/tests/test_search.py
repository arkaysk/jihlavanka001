import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import search, volumes as vol_mod  # noqa: E402


def touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()


class SearchTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def names(self, query, **kw):
        return [h.name for h in search.find([self.root], query, **kw)]

    def test_fold_ignores_case_and_diacritics(self):
        self.assertEqual(search.fold("Žltá ČUČORIEDKA"), "zlta cucoriedka")

    def test_finds_by_name_without_diacritics(self):
        touch(os.path.join(self.root, "Žltá tapeta.jpg"))
        touch(os.path.join(self.root, "iné.txt"))
        self.assertEqual(self.names("zlta"), ["Žltá tapeta.jpg"])

    def test_all_words_must_match_in_any_order(self):
        touch(os.path.join(self.root, "letná dovolenka 2026.txt"))
        touch(os.path.join(self.root, "letná fotka.txt"))
        self.assertEqual(self.names("2026 letna"), ["letná dovolenka 2026.txt"])

    def test_shallow_matches_come_first(self):
        touch(os.path.join(self.root, "a", "b", "report.txt"))
        touch(os.path.join(self.root, "report.txt"))
        paths = [h.path for h in search.find([self.root], "report")]
        self.assertEqual(paths[0], os.path.join(self.root, "report.txt"))
        self.assertEqual(len(paths), 2)

    def test_directories_are_marked(self):
        os.makedirs(os.path.join(self.root, "Fotky"))
        hit = next(search.find([self.root], "fotky"))
        self.assertTrue(hit.is_dir)

    def test_hidden_entries_are_skipped_including_their_content(self):
        touch(os.path.join(self.root, ".skryte", "tajne.txt"))
        touch(os.path.join(self.root, ".tajne.txt"))
        self.assertEqual(self.names("tajne"), [])

    def test_limit_stops_the_search(self):
        for i in range(10):
            touch(os.path.join(self.root, "subor%d.txt" % i))
        self.assertEqual(len(self.names("subor", limit=3)), 3)

    def test_cancel_stops_the_search(self):
        touch(os.path.join(self.root, "subor.txt"))
        self.assertEqual(self.names("subor", cancelled=lambda: True), [])

    def test_symlinked_directories_are_not_followed(self):
        touch(os.path.join(self.root, "real", "cielovy.txt"))
        os.symlink(os.path.join(self.root, "real"), os.path.join(self.root, "odkaz"))
        self.assertEqual(self.names("cielovy"), ["cielovy.txt"])

    def test_empty_query_finds_nothing(self):
        touch(os.path.join(self.root, "subor.txt"))
        self.assertEqual(self.names("   "), [])

    def test_roots_drop_missing_duplicate_and_nested(self):
        inner = os.path.join(self.root, "inner")
        os.makedirs(inner)
        roots = search.dedupe_roots([self.root, inner, self.root, "/nie/je/tu", None])
        self.assertEqual(roots, [self.root])

    def test_search_roots_use_home_and_mounted_data_volumes_only(self):
        data = os.path.join(self.root, "data")
        os.makedirs(data)
        home = os.path.join(self.root, "home")
        os.makedirs(home)
        volumes = [
            vol_mod.Volume("Device1", "/", role="system"),
            vol_mod.Volume("Device2", data, role="data"),
            vol_mod.Volume("Device3", None, role="data"),
        ]
        self.assertEqual(search.search_roots(volumes, home), [home, data])

    def test_display_path_uses_volume_names(self):
        data = os.path.join(self.root, "data")
        os.makedirs(os.path.join(data, "Fotky"))
        volumes = [vol_mod.Volume("Device2", data, role="data")]
        self.assertEqual(search.display_path(volumes, os.path.join(data, "Fotky")),
                         "Device2 › Fotky")

    def test_display_path_on_the_system_volume_starts_at_its_root(self):
        volumes = [vol_mod.Volume("Device1", "/", role="system")]
        self.assertEqual(search.display_path(volumes, "/home/user/dev"), "Device1 › home › user › dev")
        self.assertEqual(search.display_path(volumes, "/etc"), "/etc")      # systém neukazuje /etc


if __name__ == "__main__":
    unittest.main()
