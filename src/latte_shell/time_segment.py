"""Segment času v lište (bod 2.6): hodiny, zvonček s počtom oznámení a dátum.

Každá časť otvára svoju stránku manažéra času: hodiny časové pásma, zvonček oznámenia,
dátum kalendár.
"""
from datetime import datetime

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib  # noqa: E402


class TimeSegment(Gtk.Box):
    def __init__(self, center, on_open):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.center = center
        self.add_css_class("segment")
        self.add_css_class("time-segment")
        self.set_valign(Gtk.Align.CENTER)
        self.set_size_request(-1, 64)

        self.clock = Gtk.Label()
        self.clock.add_css_class("clock")
        self.date = Gtk.Label()
        self.date.add_css_class("dim")
        self.append(self.part(self.clock, lambda: on_open("zones")))

        self.bell_icon = Gtk.Image.new_from_icon_name("preferences-system-notifications-symbolic")
        self.bell_icon.set_pixel_size(20)
        self.bell_count = Gtk.Label()
        self.bell_count.add_css_class("bell-count")
        self.bell_count.set_valign(Gtk.Align.CENTER)
        bell = Gtk.Box(spacing=4)
        bell.append(self.bell_icon)
        bell.append(self.bell_count)
        self.append(self.part(bell, lambda: on_open("notifications")))

        self.append(self.part(self.date, lambda: on_open("calendar")))

        center.subscribe(self.update_bell)
        self.update_bell()
        self.tick()
        GLib.timeout_add_seconds(10, self.tick)

    def part(self, child, action):
        button = Gtk.Button()
        button.add_css_class("time-part")
        button.set_child(child)
        button.set_valign(Gtk.Align.FILL)
        button.connect("clicked", lambda _b: action())
        return button

    def tick(self, *_args):
        now = datetime.now()
        self.clock.set_text(now.strftime("%H:%M"))
        self.date.set_text(now.strftime("%-d. %-m. %Y"))
        return True

    def update_bell(self):
        count = self.center.count
        self.bell_count.set_text(str(count) if count else "")
        self.bell_count.set_visible(bool(count))
        self.bell_icon.set_from_icon_name(
            "notifications-disabled-symbolic" if self.center.dnd
            else "preferences-system-notifications-symbolic")
