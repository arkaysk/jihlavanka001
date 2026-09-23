import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import gi  # noqa: E402
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from latte_common import appearance, theme  # noqa: E402


class ThemeTest(unittest.TestCase):
    def test_latte_css_parses_without_errors(self):
        errors = []
        provider = Gtk.CssProvider()
        provider.connect("parsing-error", lambda _p, section, err: errors.append(
            "%s: %s" % (section.to_string(), err.message)))
        provider.load_from_path(theme.style_file())
        self.assertEqual(errors, [])

    def test_every_var_used_is_defined(self):
        import re
        with open(theme.style_file(), encoding="utf-8") as f:
            css = f.read()
        defined = set(appearance.latte_vars(appearance.resolve({})))       # premenné generuje appearance.py
        used = set(re.findall(r"var\((--[\w-]+)\)", css))
        self.assertEqual(used - defined, set())
        self.assertNotIn(":root", css, "premenné patria do motívu, nie do latte.css")

    def test_gtk4_css_with_media_query_parses_in_gtk(self):
        errors = []
        provider = Gtk.CssProvider()
        provider.connect("parsing-error", lambda _p, section, err: errors.append(
            "%s: %s" % (section.to_string(), err.message)))
        provider.load_from_string(appearance.gtk4_css(appearance.resolve({})))
        self.assertEqual(errors, [])

    def test_window_controls_css_parses_in_gtk(self):
        errors = []
        provider = Gtk.CssProvider()
        provider.connect("parsing-error", lambda _p, section, err: errors.append(
            "%s: %s" % (section.to_string(), err.message)))
        provider.load_from_string(appearance.window_controls_css(appearance.resolve({})))
        self.assertEqual(errors, [])
        self.assertIn("windowcontrols", theme.full_css())

    def test_full_css_parses_for_every_variant_and_option(self):
        combos = [
            {}, {"color.scheme": "light"}, {"color.transparency": False}, {"shape.corners": "square"},
            {"accessibility.contrast": "high"}, {"color.accent": "#3A9BD9", "color.scheme": "light"},
        ]
        for values in combos:
            errors = []
            provider = Gtk.CssProvider()
            provider.connect("parsing-error", lambda _p, section, err: errors.append(
                "%s: %s" % (section.to_string(), err.message)))
            provider.load_from_string(theme.full_css(appearance.resolve(values)))
            self.assertEqual(errors, [], values)


if __name__ == "__main__":
    unittest.main()
