import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import gi  # noqa: E402
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from latte_common import theme  # noqa: E402


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
        defined = set(re.findall(r"(--[\w-]+)\s*:", css))
        used = set(re.findall(r"var\((--[\w-]+)\)", css))
        self.assertEqual(used - defined, set())


if __name__ == "__main__":
    unittest.main()
