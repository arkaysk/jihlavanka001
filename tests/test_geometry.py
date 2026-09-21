import glob
import os
import re
import sys
import tomllib
import unittest

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, SRC)

from latte_shell import geometry  # noqa: E402


class GeometryTest(unittest.TestCase):
    def tearDown(self):
        geometry.set_bar_height(geometry.DEFAULT_BAR_HEIGHT)

    def test_default_is_within_range(self):
        self.assertLessEqual(geometry.MIN_BAR_HEIGHT, geometry.DEFAULT_BAR_HEIGHT)
        self.assertLessEqual(geometry.DEFAULT_BAR_HEIGHT, geometry.MAX_BAR_HEIGHT)
        self.assertEqual(geometry.bar_height(), geometry.DEFAULT_BAR_HEIGHT)

    def test_set_reports_whether_it_changed(self):
        self.assertTrue(geometry.set_bar_height(70))
        self.assertEqual(geometry.bar_height(), 70)
        self.assertFalse(geometry.set_bar_height(70))

    def test_out_of_range_is_clamped(self):
        geometry.set_bar_height(10)
        self.assertEqual(geometry.bar_height(), geometry.MIN_BAR_HEIGHT)
        geometry.set_bar_height(5000)
        self.assertEqual(geometry.bar_height(), geometry.MAX_BAR_HEIGHT)

    def test_nonsense_gives_the_default(self):
        for bad in (None, "abc", float("nan"), float("inf")):
            geometry.set_bar_height(70)
            geometry.set_bar_height(bad)
            self.assertEqual(geometry.bar_height(), geometry.DEFAULT_BAR_HEIGHT, repr(bad))

    def test_corner_is_a_rectangle_as_tall_as_the_bar(self):
        """Dlaždice sedia na okraji a majú hornú hranu v rovnakej výške; rohová je obdĺžnik."""
        for height in (geometry.MIN_BAR_HEIGHT, 70, geometry.MAX_BAR_HEIGHT):
            geometry.set_bar_height(height)
            self.assertEqual(geometry.corner_width(), 2 * height)
            self.assertGreater(geometry.corner_width(), geometry.bar_height())
            self.assertEqual(geometry.texture_height(), height + geometry.ARM_HEIGHT)

    def test_corner_icon_fits_and_grows_with_the_bar(self):
        sizes = []
        for height in range(geometry.MIN_BAR_HEIGHT, geometry.MAX_BAR_HEIGHT + 1, 2):
            geometry.set_bar_height(height)
            size = geometry.corner_icon_size()
            self.assertLessEqual(size, height * 0.5, "ikona je príliš veľká pri %d" % height)
            self.assertGreaterEqual(size, 20)
            sizes.append(size)
        self.assertEqual(sizes, sorted(sizes))

    def test_schema_matches_the_geometry(self):
        """Rozsah v nastaveniach a v lište sa nesmie rozísť."""
        path = os.path.join(SRC, "..", "data", "settings", "appearance.schema.toml")
        with open(path, "rb") as f:
            key = tomllib.load(f)["key"]["bar.height"]
        self.assertEqual((key["default"], key["min"], key["max"]),
                         (geometry.DEFAULT_BAR_HEIGHT, geometry.MIN_BAR_HEIGHT, geometry.MAX_BAR_HEIGHT))
        for value in (key["default"], key["min"], key["max"]):
            self.assertEqual((value - key["min"]) % key["step"], 0, "krok posuvníka nezasiahne %d" % value)

    def test_no_other_module_keeps_its_own_copy_of_the_bar_size(self):
        """Výška lišty bola opísaná v troch súboroch a je nastavenie: nikto si ju nesmie zapísať do konštanty."""
        constant = re.compile(r"^\s*(BAR_HEIGHT|SEGMENT|ICON_SEGMENT_WIDTH|CORNER\w*|TEXTURE_HEIGHT)\s*=\s*\d+", re.MULTILINE)
        frozen = re.compile(r"^\w+\s*=\s*.*\b(geometry\.)?(bar_height|corner_width|texture_height)\(\)", re.MULTILINE)
        for path in glob.glob(os.path.join(SRC, "latte_shell", "*.py")):
            if os.path.basename(path) == "geometry.py":
                continue
            with open(path, encoding="utf-8") as f:
                text = f.read()
            self.assertIsNone(constant.search(text), path)
            self.assertIsNone(frozen.search(text), "%s: výška lišty skopírovaná do konštanty pri importe" % path)


if __name__ == "__main__":
    unittest.main()
