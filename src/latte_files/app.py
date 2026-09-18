#!/usr/bin/env python3
"""latte-files: správca súborov LatteOS."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib  # noqa: E402

from latte_common import volumes as vol_mod  # noqa: E402

ROOT_NAME = "Tento počítač"


def free_space(path):
    try:
        st = os.statvfs(path)
        return GLib.format_size(st.f_bavail * st.f_frsize)
    except OSError:
        return ""


class Window(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Súbory")
        self.set_default_size(1050, 680)

        self.volumes = vol_mod.list_volumes()
        self.volume = None      # None = koreň (Tento počítač)
        self.path = None        # kde sme
        self.root = None        # hranica, nad ktorú sa nedá ísť
        self.history = []
        self.forward = []

        # ---------- titulok ----------
        header = Gtk.HeaderBar()
        self.set_titlebar(header)

        self.btn_back = Gtk.Button(icon_name="go-previous-symbolic")
        self.btn_back.connect("clicked", self.on_back)
        header.pack_start(self.btn_back)

        self.btn_fwd = Gtk.Button(icon_name="go-next-symbolic")
        self.btn_fwd.connect("clicked", self.on_forward)
        header.pack_start(self.btn_fwd)

        self.btn_up = Gtk.Button(icon_name="go-up-symbolic")
        self.btn_up.connect("clicked", self.on_up)
        header.pack_start(self.btn_up)

        btn_home = Gtk.Button(icon_name="go-home-symbolic")
        btn_home.connect("clicked", lambda _b: self.go_root())
        header.pack_start(btn_home)

        self.crumbs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        header.set_title_widget(self.crumbs)

        # ---------- telo ----------
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(box)

        side_scroll = Gtk.ScrolledWindow()
        side_scroll.set_size_request(240, -1)
        side_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        side_scroll.set_child(side_box)

        head_btn = Gtk.Button()
        head_btn.add_css_class("flat")
        head_lbl = Gtk.Label(label=ROOT_NAME, xalign=0)
        head_lbl.add_css_class("heading")
        head_btn.set_child(head_lbl)
        head_btn.set_margin_top(10)
        head_btn.set_margin_start(6)
        head_btn.set_margin_end(6)
        head_btn.connect("clicked", lambda _b: self.go_root())
        side_box.append(head_btn)

        self.side = Gtk.ListBox()
        self.side.connect("row-activated", self.on_side)
        side_box.append(self.side)

        box.append(side_scroll)
        box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        main_scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        self.list = Gtk.ListBox()
        self.list.connect("row-activated", self.on_entry)
        main_scroll.set_child(self.list)
        box.append(main_scroll)

        self.fill_sidebar()
        self.go_root(record=False)

    # ---------- bočný panel ----------
    def fill_sidebar(self):
        for v in self.volumes:
            row = Gtk.ListBoxRow()
            row.volume = v
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            inner.set_margin_top(7)
            inner.set_margin_bottom(7)
            inner.set_margin_start(14)
            inner.set_margin_end(12)
            title = Gtk.Label(label=v.name, xalign=0)
            title.add_css_class("heading")
            if v.removable:
                note = "výmenné · " + v.size
            elif v.role == "system":
                note = "systémový zväzok"
            else:
                note = v.size
            sub = Gtk.Label(label=note, xalign=0)
            sub.add_css_class("dim-label")
            inner.append(title)
            inner.append(sub)
            row.set_child(inner)
            self.attach_menu(row, v)
            self.side.append(row)

    def reload_sidebar(self):
        row = self.side.get_first_child()
        while row is not None:
            self.side.remove(row)
            row = self.side.get_first_child()
        self.fill_sidebar()

    def on_side(self, _box, row):
        self.go_volume(row.volume)

    # ---------- premenovanie zväzku ----------
    def attach_menu(self, widget, volume):
        gesture = Gtk.GestureClick()
        gesture.set_button(3)          # pravé tlačidlo
        gesture.connect("pressed", self.on_right_click, volume)
        widget.add_controller(gesture)

    def on_right_click(self, _gesture, _n, _x, _y, volume):
        self.ask_rename(volume)

    def ask_rename(self, volume):
        dialog = Gtk.Window(transient_for=self, modal=True, title="Premenovať zväzok")
        dialog.set_default_size(340, -1)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(18)
        box.set_margin_bottom(18)
        box.set_margin_start(18)
        box.set_margin_end(18)
        dialog.set_child(box)

        entry = Gtk.Entry(text=volume.name)
        box.append(entry)

        note = Gtk.Label(label="Interná identita zväzku sa nemení.", xalign=0)
        note.add_css_class("dim-label")
        box.append(note)

        row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=8, halign=Gtk.Align.END
        )
        cancel = Gtk.Button(label="Zrušiť")
        cancel.connect("clicked", lambda _b: dialog.destroy())
        ok = Gtk.Button(label="Premenovať")
        ok.add_css_class("suggested-action")

        def apply(_widget):
            if vol_mod.rename(volume, entry.get_text()):
                self.reload_sidebar()
                self.refresh()
            dialog.destroy()

        ok.connect("clicked", apply)
        entry.connect("activate", apply)
        row.append(cancel)
        row.append(ok)
        box.append(row)

        dialog.present()

    # ---------- navigácia ----------
    def snapshot(self):
        return (self.volume, self.path, self.root)

    def restore(self, state):
        self.volume, self.path, self.root = state
        self.refresh()

    def record(self):
        self.history.append(self.snapshot())
        self.forward.clear()

    def go_root(self, record=True):
        if record and self.volume is not None:
            self.record()
        self.volume = None
        self.path = None
        self.root = None
        self.refresh()

    def go_volume(self, volume, record=True):
        if record:
            self.record()
        self.volume = volume
        self.path = volume.path
        self.root = volume.path
        self.refresh()

    def go_path(self, path, root=None, record=True):
        if record:
            self.record()
        if root is not None:
            self.root = root
        self.path = path
        self.refresh()

    def on_back(self, _btn):
        if not self.history:
            return
        self.forward.append(self.snapshot())
        self.restore(self.history.pop())

    def on_forward(self, _btn):
        if not self.forward:
            return
        self.history.append(self.snapshot())
        self.restore(self.forward.pop())

    def on_up(self, _btn):
        if self.volume is None:
            return
        if self.path == self.root:
            if self.root != self.volume.path:
                self.record()
                self.path = self.volume.path
                self.root = self.volume.path
                self.refresh()
            else:
                self.go_root()
            return
        self.go_path(os.path.dirname(self.path))

    def on_entry(self, _box, row):
        if row.volume is not None:
            self.go_volume(row.volume)
            return
        target = row.target
        if not target:
            return
        if os.path.isdir(target):
            if self.path == self.volume.path and self.volume.entries() is not None:
                self.go_path(target, root=target)
            else:
                self.go_path(target)
            return
        self.open_object(target)

    # ---------- akcie nad objektom ----------
    def open_object(self, path):
        """OPEN(objekt -> aplikácia). Dnes cez predvolenú aplikáciu systému.
        Neskôr tu vznikne Action Object a capability."""
        try:
            gfile = Gio.File.new_for_path(path)
            info = gfile.query_info("standard::content-type", 0, None)
            ctype = info.get_content_type()
            app = Gio.AppInfo.get_default_for_type(ctype, False) if ctype else None
            if app is None:
                self.notify("Pre tento typ súboru nie je nastavená aplikácia.")
                return
            app.launch([gfile], None)
        except GLib.Error as err:
            self.notify("Súbor sa nepodarilo otvoriť: " + err.message)

    def notify(self, text):
        dialog = Gtk.AlertDialog()
        dialog.set_message(text)
        dialog.show(self)

    # ---------- breadcrumb ----------
    def crumb_button(self, label, action):
        btn = Gtk.Button(label=label)
        btn.add_css_class("flat")
        btn.connect("clicked", action)
        return btn

    def build_crumbs(self):
        child = self.crumbs.get_first_child()
        while child is not None:
            self.crumbs.remove(child)
            child = self.crumbs.get_first_child()

        self.crumbs.append(self.crumb_button(ROOT_NAME, lambda _b: self.go_root()))
        if self.volume is None:
            return

        vol = self.volume
        self.crumbs.append(Gtk.Label(label="›"))
        self.crumbs.append(
            self.crumb_button(vol.name, lambda _b, v=vol: self.go_volume(v))
        )

        if self.path == vol.path:
            return

        if self.root != vol.path:
            base = self.root
            self.crumbs.append(Gtk.Label(label="›"))
            self.crumbs.append(
                self.crumb_button(
                    os.path.basename(self.root),
                    lambda _b, p=self.root: self.go_path(p, root=p),
                )
            )
        else:
            base = vol.path

        rel = os.path.relpath(self.path, base)
        if rel == ".":
            return
        current = base
        for part in rel.split(os.sep):
            current = os.path.join(current, part)
            self.crumbs.append(Gtk.Label(label="›"))
            self.crumbs.append(
                self.crumb_button(part, lambda _b, p=current: self.go_path(p))
            )

    # ---------- výpis ----------
    def add_row(self, text, subtext, target, volume=None):
        row = Gtk.ListBoxRow()
        row.target = target
        row.volume = volume
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
        return row

    def clear_list(self):
        row = self.list.get_first_child()
        while row is not None:
            self.list.remove(row)
            row = self.list.get_first_child()

    def refresh(self):
        self.clear_list()
        self.build_crumbs()
        self.btn_back.set_sensitive(bool(self.history))
        self.btn_fwd.set_sensitive(bool(self.forward))
        self.btn_up.set_sensitive(self.volume is not None)

        # koreň: zoznam zväzkov
        if self.volume is None:
            for v in self.volumes:
                note = free_space(v.path)
                if note:
                    note = "voľné " + note + " z " + v.size
                else:
                    note = v.size
                row = self.add_row(v.name, note, None, volume=v)
                self.attach_menu(row, v)
            return

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
                self.add_row(entry.name, GLib.format_size(size), entry.path)


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.latteos.Files")

    def do_activate(self):
        Window(self).present()


if __name__ == "__main__":
    App().run(sys.argv)