"""Zoznam otvorených okien v strede lišty."""
import sys

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio  # noqa: E402

from latte_shell.foreign_toplevel import ForeignToplevels  # noqa: E402


def icon_for(app_id):
    for name in (app_id, app_id.lower()):
        if not name:
            continue
        try:
            info = Gio.DesktopAppInfo.new(name + ".desktop")
        except TypeError:               # PyGObject: konštruktor vrátil NULL
            continue
        if info.get_icon() is not None:
            return info.get_icon()
    return None


class TaskButton(Gtk.Button):
    def __init__(self, top, on_click):
        super().__init__()
        self.top = top
        self.icon_app_id = None
        self.add_css_class("task")
        self.set_valign(Gtk.Align.CENTER)

        inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.icon = Gtk.Image()
        self.icon.set_pixel_size(24)
        self.label = Gtk.Label(xalign=0)
        self.label.set_ellipsize(3)             # Pango.EllipsizeMode.END
        self.label.set_max_width_chars(22)
        inner.append(self.icon)
        inner.append(self.label)
        self.set_child(inner)
        self.connect("clicked", lambda _b: on_click(self.top))
        self.update()

    def update(self):
        title = self.top.title or self.top.app_id
        self.label.set_text(title)
        self.set_tooltip_text(title)
        if self.icon_app_id != self.top.app_id:
            self.icon_app_id = self.top.app_id
            gicon = icon_for(self.top.app_id)
            if gicon is not None:
                self.icon.set_from_gicon(gicon)
            else:
                self.icon.set_from_icon_name("application-x-executable")
        for css, on in (("active", self.top.activated), ("minimized", self.top.minimized)):
            if on:
                self.add_css_class(css)
            else:
                self.remove_css_class(css)


class TaskList(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.add_css_class("segment")
        self.set_hexpand(True)
        self.set_size_request(-1, 64)
        self.set_valign(Gtk.Align.CENTER)

        self.buttons = {}
        self.watcher = ForeignToplevels(self.changed, self.closed, self.unavailable)
        self.watcher.start()

    def changed(self, top):
        button = self.buttons.get(top.id)
        if button is None:
            button = TaskButton(top, self.clicked)
            button.set_margin_start(6)
            self.buttons[top.id] = button
            self.append(button)
        else:
            button.update()

    def closed(self, top):
        button = self.buttons.pop(top.id, None)
        if button is not None:
            self.remove(button)

    def unavailable(self, reason):
        # bez tichej degradácie: povedať, prečo zoznam nefunguje
        print("latte-shell: zoznam okien nie je dostupný:", reason, file=sys.stderr)
        for button in self.buttons.values():
            self.remove(button)
        self.buttons.clear()
        note = Gtk.Label(label="Zoznam okien nie je dostupný: " + reason)
        note.add_css_class("dim")
        note.set_hexpand(True)
        self.append(note)

    def clicked(self, top):
        if top.activated and not top.minimized:
            self.watcher.minimize(top)
        else:
            if top.minimized:
                self.watcher.unminimize(top)
            self.watcher.activate(top)
