import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import paths, wallpaper  # noqa: E402


class WallpaperTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = wallpaper.CONFIG_DIR
        wallpaper.CONFIG_DIR = os.path.join(self._tmp.name, "config")
        self.image = os.path.join(self._tmp.name, "moja tapeta čučoriedky.jpg")
        with open(self.image, "wb") as f:
            f.write(b"\xff\xd8\xff")

    def tearDown(self):
        wallpaper.CONFIG_DIR = self._old
        self._tmp.cleanup()

    def test_system_wallpaper_ships_with_the_theme(self):
        self.assertTrue(os.path.isfile(wallpaper.system_path()), wallpaper.system_path())

    def test_without_settings_desktop_uses_system_wallpaper(self):
        self.assertIsNone(wallpaper.user_path())
        self.assertEqual(wallpaper.desktop_path(), wallpaper.system_path())

    def test_user_wallpaper_wins_and_roundtrips_odd_paths(self):
        wallpaper.save_appearance(self.image, "contain")
        self.assertEqual(wallpaper.user_path(), self.image)
        self.assertEqual(wallpaper.desktop_path(), self.image)
        self.assertEqual(wallpaper.desktop_fit(), "contain")

    def test_missing_user_file_falls_back_to_system(self):
        wallpaper.save_appearance(self.image)
        os.unlink(self.image)
        self.assertEqual(wallpaper.desktop_path(), wallpaper.system_path())

    def test_reset_returns_system_wallpaper(self):
        wallpaper.save_appearance(self.image)
        wallpaper.save_appearance(None)
        self.assertEqual(wallpaper.desktop_path(), wallpaper.system_path())

    def test_broken_or_odd_settings_are_ignored(self):
        os.makedirs(wallpaper.CONFIG_DIR)
        with open(wallpaper.appearance_file(), "w") as f:
            f.write("[wallpaper]\npath = 5\nfit = 'sideways'\n")
        self.assertEqual(wallpaper.load_appearance(), {"wallpaper": None, "fit": "cover"})
        with open(wallpaper.appearance_file(), "w") as f:
            f.write("toto nie je toml [[[")
        self.assertEqual(wallpaper.desktop_path(), wallpaper.system_path())

    def test_relative_path_is_not_accepted(self):
        os.makedirs(wallpaper.CONFIG_DIR)
        with open(wallpaper.appearance_file(), "w") as f:
            f.write("[wallpaper]\npath = 'tapeta.jpg'\n")
        self.assertIsNone(wallpaper.load_appearance()["wallpaper"])

    def test_blurred_copy_keeps_size(self):
        blurred = wallpaper.blurred_pixbuf(wallpaper.system_path())
        import gi
        gi.require_version("GdkPixbuf", "2.0")
        from gi.repository import GdkPixbuf
        _fmt, width, height = GdkPixbuf.Pixbuf.get_file_info(wallpaper.system_path())
        self.assertEqual((blurred.get_width(), blurred.get_height()), (width, height))


class PathsTest(unittest.TestCase):
    def test_env_override(self):
        os.environ["LATTEOS_DATA"] = "/somewhere"
        try:
            self.assertEqual(paths.data_dir(), "/somewhere")
        finally:
            del os.environ["LATTEOS_DATA"]

    def test_repo_data_is_found_in_development(self):
        self.assertTrue(os.path.isfile(os.path.join(paths.data_dir(), "styles", "latte.css")))


if __name__ == "__main__":
    unittest.main()
