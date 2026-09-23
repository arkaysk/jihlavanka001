"""Spoločné prvky rozhrania LatteOS: tapeta, hodiny, avatar.

Používa ich lišta aj prihlasovacia obrazovka, aby vyzerali ako jeden produkt.
Vzhľad drží data/styles/latte.css.
"""
from datetime import datetime

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

from latte_common import wallpaper  # noqa: E402

_FITS = {
    "cover": Gtk.ContentFit.COVER,
    "contain": Gtk.ContentFit.CONTAIN,
    "fill": Gtk.ContentFit.FILL,
}


class Wallpaper(Gtk.Picture):
    """Tapeta cez celú plochu. Ak sa súbor nedá načítať, ostane podklad z témy."""

    def __init__(self, path=None, fit="cover", blurred=False):
        super().__init__()
        self.add_css_class("latte-wallpaper")
        self.set_can_shrink(True)
        self.set_can_target(False)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_path(path, fit, blurred)

    def set_path(self, path, fit="cover", blurred=False):
        self.set_content_fit(_FITS.get(fit, Gtk.ContentFit.COVER))
        self.set_paintable(_texture(path, blurred))


def _texture(path, blurred):
    if not path:
        return None
    try:
        if blurred:
            return Gdk.Texture.new_for_pixbuf(wallpaper.blurred_pixbuf(path))
        return Gdk.Texture.new_from_filename(path)
    except GLib.Error as err:
        print("latte-wallpaper: %s sa nedá načítať: %s" % (path, err.message))
        return None


class ClockSegment(Gtk.Button):
    """Hodiny a dátum v segmente, ako v lište."""

    def __init__(self):
        super().__init__()
        self.add_css_class("segment")
        self.set_size_request(200, 64)
        self.set_valign(Gtk.Align.CENTER)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_halign(Gtk.Align.CENTER)
        self.clock = Gtk.Label()
        self.clock.add_css_class("clock")
        self.date = Gtk.Label()
        self.date.add_css_class("dim")
        box.append(self.clock)
        box.append(self.date)
        self.set_child(box)
        self.tick()
        GLib.timeout_add_seconds(10, self.tick)

    def tick(self, *_args):
        now = datetime.now()
        self.clock.set_text(now.strftime("%H:%M"))
        self.date.set_text(now.strftime("%-d. %-m. %Y"))
        return True


def initials(name):
    parts = [p for p in name.replace("_", " ").replace(".", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:1].upper()
    return (parts[0][:1] + parts[-1][:1]).upper()


class Avatar(Gtk.Box):
    """Kruhový avatar: fotka, ak je čitateľná, inak iniciálky."""

    def __init__(self, name, image_path=None, size=40):
        super().__init__()
        self.add_css_class("avatar")
        self.add_css_class("large" if size >= 80 else "small")
        self.set_size_request(size, size)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_overflow(Gtk.Overflow.HIDDEN)       # fotka sa oreže do kruhu
        if image_path:
            try:
                picture = Gtk.Picture.new_for_paintable(Gdk.Texture.new_from_filename(image_path))
                picture.set_content_fit(Gtk.ContentFit.COVER)
                picture.set_can_shrink(True)
                picture.set_hexpand(True)
                picture.set_vexpand(True)
                self.append(picture)
                return
            except (GLib.Error, OSError):
                pass
        label = Gtk.Label(label=initials(name))
        label.set_hexpand(True)
        label.set_vexpand(True)
        self.append(label)
