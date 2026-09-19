"""Téma LatteOS: každý komponent si ju načíta odtiaľto, nemá vlastné CSS."""
import os
import sys

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio  # noqa: E402

from latte_common import paths  # noqa: E402


def style_file():
    return os.path.join(paths.data_dir(), "styles", "latte.css")


def _report(_provider, section, error):
    print("latte-theme:", section.to_string() + ":", error.message, file=sys.stderr)


def load(display):
    # tmavé prostredie pre všetky komponenty; farby a tvary drží latte.css
    Gtk.Settings.get_for_display(display).set_property("gtk-application-prefer-dark-theme", True)
    provider = Gtk.CssProvider()
    provider.connect("parsing-error", _report)
    provider.load_from_file(Gio.File.new_for_path(style_file()))
    Gtk.StyleContext.add_provider_for_display(
        display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
