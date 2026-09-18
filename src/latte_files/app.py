#!/usr/bin/env python3
"""latte-files: správca súborov LatteOS. Prvá verzia."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib  # noqa: E402

from latte_common import volumes as vol_mod  # noqa: E402


class Window(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Prieskumník")
        self.set_default_size(1000, 650)

        self.volumes = vol_mod.list_volumes()
        self.volume = None
        self.path = None

        header = Gtk.HeaderBar()
        self.set_titlebar(header)
        self.crumb = Gtk.Label(label="Zväzky", xalign=0)
        header.set_title_widget(self.crumb)

        back = Gtk.Button(label="Späť")
        back.connect("clicked", self.on_back)
        header.pack_start(back)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(box)

        side_scroll = Gtk.ScrolledWindow()
        side_scroll.set_size_request(230, -1)
        self.side = Gtk.ListBox()
        self.side.connect("row-activated", self.on_volume)
        side_scroll.set_child(self.side)
        box.append(side_scroll)
        box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        main_scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        self.list = Gtk.ListBox()
        self.list.connect("row-activated", self.on_entry)
        main_scroll.set_child(self.list)
        box.append(main_scroll)

        self.fill_sidebar()
        if self.volumes:
            self.open_volume(self.volumes[0])

    # ---------- bočný panel ----------
    def fill_sidebar(self):
        for v in self.volumes:
            row = Gtk.ListBoxRow()
            row.volume = v
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            inner.set_margin_top(8)
            inner.set_margin_bottom(8)
            inner.set_margin_start(12)
            inner.set_margin_end(12)
            title = Gtk.Label(label=v.name, xalign=0)
            title.add_css_class("heading")
            note = "systémový zväzok" if v.role == "system" else v.size
            if v.removable:
                note = "výmenné · " + v.size
            sub = Gtk.Label(label=note, xalign=0)
            sub.add_css_class("dim-label")
            inner.append(title)
            inner.append(sub)
            row.set_child(inner)
            self.side.append(row)

    # ---------- navigácia ----------
    def open_volume(self, volume):
        self.volume = volume
        self.path = volume.path
        self.root = volume.path          # hranica, nad ktorú sa nedá ísť
        self.refresh()

    def on_volume(self, _box, row):
        self.open_volume(row.volume)

    def on_back(self, _btn):
        if not self.volume:
            return
        if self.path == self.root:
            # sme v koreni priečinka Apps/Users/Shared -> späť na zväzok
            if self.root != self.volume.path:
                self.root = self.volume.path
                self.path = self.volume.path
                self.refresh()
            return
        self.path = os.path.dirname(self.path)
        self.refresh()

    def on_entry(self, _box, row):
        target = row.target
        if not target or not os.path.isdir(target):
            return
        # vstup do systémového miesta (Apps, Users, Shared) posúva hranicu
        if self.path == self.volume.path and self.volume.entries() is not None:
            self.root = target
        self.path = target
        self.refresh()

    # ---------- výpis ----------
    def add_row(self, text, subtext, target):
        row = Gtk.ListBoxRow()
        row.target = target
        line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        line.set_margin_top(7)
        line.set_margin_bottom(7)
        line.set_margin_start(14)
        line.set_margin_end(14)
        name = Gtk.Label(label=text, xalign=0, hexpand=True)
        info = Gtk.Label(label=subtext, xalign=1)
        info.add_css_class("dim-label")
        line.append(name)
        line.append(info)
        row.set_child(line)
        self.list.append(row)

    def refresh(self):
        while True:
            row = self.list.get_first_child()
            if row is None:
                break
            self.list.remove(row)

        base = os.path.dirname(self.root) if self.root != self.volume.path else self.volume.path
        rel = os.path.relpath(self.path, base)
        crumb = self.volume.name if self.path == self.volume.path else self.volume.name + "/" + rel
        self.crumb.set_text(crumb)

        # koreň systémového zväzku: iba vybrané miesta
        if self.path == self.volume.path:
            custom = self.volume.entries()
            if custom is not None:
                for label, target in custom:
                    self.add_row(label, "priečinok", target)
                return

        if self.path != self.root:
            self.add_row("..", "", os.path.dirname(self.path))

        try:
            items = sorted(
                os.scandir(self.path),
                key=lambda e: (not e.is_dir(), e.name.lower()),
            )
        except PermissionError:
            self.add_row("Prístup zamietnutý", "", None)
            return

        for entry in items:
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                self.add_row(entry.name, "priečinok", entry.path)
            else:
                try:
                    size = entry.stat().st_size
                except OSError:
                    size = 0
                self.add_row(entry.name, GLib.format_size(size), None)


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.latteos.Files")

    def do_activate(self):
        Window(self).present()


if __name__ == "__main__":
    App().run(sys.argv)