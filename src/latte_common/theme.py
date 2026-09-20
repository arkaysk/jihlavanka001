"""Téma LatteOS: každý komponent si ju načíta odtiaľto, nemá vlastné CSS.

CSS pozostáva z premenných --latte-* (generuje ich appearance.py z motívu a nastavení Prispôsobenia)
a z pravidiel v data/styles/latte.css. Keď používateľ zmení nastavenie vzhľadu, načíta sa CSS znova
a komponent sa prekreslí bez reštartu.
"""
import os
import sys

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib  # noqa: E402

from latte_common import appearance, paths, settings  # noqa: E402

APPEARANCE_FILE = "appearance.toml"
_original = {}                  # pôvodné hodnoty GTK nastavení, aby sa vedeli vrátiť (písmo, mierka)
_monitors = []                  # sledovanie nastavení musí žiť tak dlho ako komponent


def style_file():
    return os.path.join(paths.data_dir(), "styles", "latte.css")


def full_css(tokens=None):
    """Premenné z motívu + pravidlá z latte.css: presne to, čo dostane každý komponent."""
    tokens = tokens or appearance.current_tokens()
    with open(style_file(), encoding="utf-8") as f:
        return appearance.css_variables(tokens) + "\n" + appearance.titlebar_css(tokens) + appearance.window_controls_css(tokens) + "\n" + f.read()


def _report(_provider, section, error):
    print("latte-theme:", section.to_string() + ":", error.message, file=sys.stderr)


def _apply_settings(display, tokens):
    """Nastavenia GTK, ktoré patria k vzhľadu: tmavý režim, písmo, mierka textu, tlačidlá okien."""
    gtk = Gtk.Settings.get_for_display(display)
    for name in ("gtk-font-name", "gtk-xft-dpi", "gtk-decoration-layout"):
        _original.setdefault(name, gtk.get_property(name))
    gtk.set_property("gtk-application-prefer-dark-theme", tokens.scheme == "dark")
    gtk.set_property("gtk-font-name", "%s 11" % tokens.font_family if tokens.font_family else _original["gtk-font-name"])
    gtk.set_property("gtk-xft-dpi", round(96 * 1024 * tokens.font_scale) if abs(tokens.font_scale - 1.0) > 1e-9
                     else _original["gtk-xft-dpi"])
    gtk.set_property("gtk-decoration-layout", appearance.BUTTON_LAYOUT[tokens.buttons])


def load(display, live=True):
    """Načíta tému pre daný displej. live=True: zmena nastavení vzhľadu sa prejaví hneď.

    Vráti poskytovateľa CSS. Problémy s nastaveniami alebo motívom sa hlásia na stderr,
    použijú sa predvolené hodnoty.
    """
    tokens = appearance.current_tokens()
    for problem in tokens.problems:
        print("latte-theme:", problem, file=sys.stderr)
    _apply_settings(display, tokens)

    provider = Gtk.CssProvider()
    provider.connect("parsing-error", _report)
    provider.load_from_string(full_css(tokens))
    Gtk.StyleContext.add_provider_for_display(display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    if live:
        def reload():
            fresh = appearance.current_tokens()
            _apply_settings(display, fresh)
            provider.load_from_string(full_css(fresh))

        try:
            _monitors.append(settings.watch([APPEARANCE_FILE], reload))
        except (OSError, GLib.Error) as err:
            # napr. prihlasovacia obrazovka (používateľ greetd): domov nemá, živá zmena tam nedáva zmysel
            print("latte-theme: zmeny vzhľadu sa nesledujú:", err, file=sys.stderr)
    return provider
