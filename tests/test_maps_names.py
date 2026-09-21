import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_shell import bar_texture, maps  # noqa: E402


class CornerNamesTest(unittest.TestCase):
    def test_every_corner_has_a_name_and_a_details_button(self):
        """Zatvorená dlaždica nemá text; názov a tlačidlo do podrobností sú v otvorenom popupe."""
        kinds = {kind for kind, _key, _right in bar_texture.TILES}
        self.assertEqual(set(maps.NAMES), kinds)
        self.assertEqual(set(maps.DETAILS), kinds)
        for kind in kinds:
            icon, text = maps.DETAILS[kind]
            self.assertTrue(maps.NAMES[kind] and icon and text)


if __name__ == "__main__":
    unittest.main()
