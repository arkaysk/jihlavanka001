import glob
import os
import re
import sys
import unittest

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, SRC)

from latte_shell import geometry  # noqa: E402


class GeometryTest(unittest.TestCase):
    def test_every_tile_is_as_tall_as_the_bar(self):
        """Dlaždice sedia na okraji a majú hornú hranu v rovnakej výške."""
        self.assertEqual(geometry.SEGMENT, geometry.BAR_HEIGHT)
        self.assertEqual(geometry.CORNER_HEIGHT, geometry.BAR_HEIGHT)

    def test_corner_is_wider_than_tall(self):
        self.assertGreater(geometry.CORNER_WIDTH, geometry.CORNER_HEIGHT)

    def test_no_other_module_defines_its_own_bar_size(self):
        """Výška lišty bola opísaná v troch súboroch a rohy vyčnievali nad segmenty."""
        pattern = re.compile(r"^\s*(BAR_HEIGHT|SEGMENT|ICON_SEGMENT_WIDTH|CORNER\w*)\s*=\s*\d+", re.MULTILINE)
        for path in glob.glob(os.path.join(SRC, "latte_shell", "*.py")):
            if os.path.basename(path) == "geometry.py":
                continue
            with open(path, encoding="utf-8") as f:
                self.assertIsNone(pattern.search(f.read()), path)


if __name__ == "__main__":
    unittest.main()
