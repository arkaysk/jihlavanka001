#!/usr/bin/env python3
"""latte-files: správca súborov LatteOS (ForkLift model)."""
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib, Gdk  # noqa: E402

from latte_common import theme, volumes as vol_mod  # noqa: E402

ROOT_NAME = "Tento počítač"


def free_space(path):
    try:
        st = os.statvfs(path)
        return GLib.format_size(st.f_bavail * st.f_frsize)
    except OSError:
        return ""


def mtime(path):
    try:
        stamp = GLib.DateTime.new_from_unix_local(int(os.path.getmtime(path)))
        return stamp.format("%-d. %-m. %Y %H:%M")
    except (OSError, TypeError):
        return ""


# ------------------------------------------------------------------ panel
class Pane(Gtk.Box):
    def __init__(self, window, volumes):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("pane")
        self.win = window
        self.volumes = volumes

        self.volume = None
        self.path = None
        self.root = None
        self.history = []
        self.forward = []

        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        head.add_css_class("pane-head")
        self.crumbs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.text_path = Gtk.Label(xalign=0)
        self.text_path.set_ellipsize(3)
        self.free = Gtk.Label(xalign=1)
        self.free.add_css_class("dim-label")
        head.append(self.crumbs)
        head.append(self.text_path)
        spacer = Gtk.Box(hexpand=True)
        head.append(spacer)
        head.append(self.free)
        self.append(head)

        scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        self.list = Gtk.ListBox()
        self.list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list.connect("row-activated", self.on_activate)
        self.list.connect("row-selected", lambda *_a: self.win.update_detail())
        scroll.set_child(self.list)
        self.append(scroll)

        context = Gtk.GestureClick()
        context.set_button(3)
        context.connect("pressed", self.on_context)
        self.list.add_controller(context)

        click = Gtk.GestureClick()
        click.connect("pressed", lambda *_a: self.win.set_active(self))
        self.add_controller(click)

        self.go_root(record=False)

    # -------- navigácia --------
    def snapshot(self):
        return (self.volume, self.path, self.root)

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

    def back(self):
        if not self.history:
            return
        self.forward.append(self.snapshot())
        self.volume, self.path, self.root = self.history.pop()
        self.refresh()

    def ahead(self):
        if not self.forward:
            return
        self.history.append(self.snapshot())
        self.volume, self.path, self.root = self.forward.pop()
        self.refresh()

    def up(self):
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

    def on_activate(self, _box, row):
        self.win.set_active(self)
        self.open_row(row)

    def open_selected(self):
        row = self.list.get_selected_row()
        if row is not None:
            self.open_row(row)

    def open_row(self, row):
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
        self.win.open_object(target)

    # -------- výber --------
    def selected(self):
        row = self.list.get_selected_row()
        if row is None or row.target is None:
            return None
        return row.target

    def can_write(self):
        return self.volume is not None and self.path is not None

    def at_fixed_root(self):
        """Koreň zväzku, ktorý ukazuje len vybrané miesta (systémový zväzok)."""
        return (
            self.volume is not None
            and self.path == self.volume.path
            and self.volume.entries() is not None
        )

    # -------- kontextové menu --------
    def on_context(self, _gesture, _n, x, y):
        row = self.list.get_row_at_y(int(y))
        if row is not None and row.volume is not None:
            return                      # zväzok má vlastné menu (premenovanie)
        self.win.set_active(self)

        if row is not None and row.target is not None and row.kind != "parent":
            self.list.select_row(row)
            model = self.item_menu(row.kind)
        elif self.can_write() and not self.at_fixed_root():
            model = self.blank_menu()
        else:
            return
        self.popup_menu(model, x, y)

    def item_menu(self, kind):
        groups = [[("Otvoriť", self.open_selected)]]
        if kind == "item":
            groups.append([
                ("Premenovať", self.win.do_rename),
                ("Kopírovať do druhého panela", self.win.do_copy),
                ("Presunúť do druhého panela", self.win.do_move),
            ])
            groups.append([("Do koša", self.win.do_trash)])
        return groups

    def blank_menu(self):
        return [[("Nový priečinok", self.win.do_mkdir)]]

    def popup_menu(self, groups, x, y):
        # Vlastný popover namiesto Gtk.PopoverMenu: ten má v GTK 4.22 pri
        # prvom otvorení s oddielmi orezanú výšku (posledná položka zmizne).
        popover = Gtk.Popover()
        popover.add_css_class("context-menu")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        for group in groups:
            if box.get_first_child() is not None:
                box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
            for label, action in group:
                btn = Gtk.Button(label=label)
                btn.add_css_class("flat")
                btn.get_child().set_xalign(0)
                btn.connect("clicked", lambda _b, a=action: (popover.popdown(), a()))
                box.append(btn)
        popover.set_child(box)
        first = box.get_first_child()

        spot = Gdk.Rectangle()
        spot.x, spot.y, spot.width, spot.height = int(x), int(y), 1, 1
        popover.set_parent(self.list)
        popover.set_has_arrow(False)
        popover.set_halign(Gtk.Align.START)
        popover.set_pointing_to(spot)
        popover.connect("closed", lambda p: GLib.idle_add(p.unparent))
        popover.popup()
        first.grab_focus()

    # -------- breadcrumb --------
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

        show = self.win.mode != "classic"
        self.crumbs.set_visible(show)
        self.text_path.set_visible(not show)

        if not show:
            if self.volume is None:
                self.text_path.set_text(ROOT_NAME)
            else:
                base = os.path.dirname(self.root) if self.root != self.volume.path else self.volume.path
                rel = os.path.relpath(self.path, base)
                self.text_path.set_text(
                    self.volume.name if self.path == self.volume.path
                    else self.volume.name + "/" + rel
                )
            return

        self.crumbs.append(self.crumb_button(ROOT_NAME, lambda _b: self.go_root()))
        if self.volume is None:
            return

        vol = self.volume
        self.crumbs.append(Gtk.Label(label="›"))
        self.crumbs.append(self.crumb_button(vol.name, lambda _b, v=vol: self.go_volume(v)))
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

    # -------- výpis --------
    def add_row(self, text, size, date, target, volume=None, is_dir=False, kind="item"):
        # kind: item = súbor alebo priečinok, fixed = pevné miesto v koreni
        # systémového zväzku (len otvoriť), parent = riadok „..“
        row = Gtk.ListBoxRow()
        row.target = target
        row.volume = volume
        row.is_dir = is_dir
        row.kind = kind
        line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        line.set_margin_top(5)
        line.set_margin_bottom(5)
        line.set_margin_start(12)
        line.set_margin_end(12)

        icon_name = "folder-symbolic" if is_dir else "text-x-generic-symbolic"
        if volume is not None:
            icon_name = "drive-harddisk-symbolic"
        icon = Gtk.Image.new_from_icon_name(icon_name)
        line.append(icon)

        name = Gtk.Label(label=text, xalign=0, hexpand=True)
        name.set_ellipsize(3)
        line.append(name)

        size_lbl = Gtk.Label(label=size, xalign=1)
        size_lbl.add_css_class("dim-label")
        size_lbl.set_size_request(90, -1)
        line.append(size_lbl)

        date_lbl = Gtk.Label(label=date, xalign=1)
        date_lbl.add_css_class("dim-label")
        date_lbl.set_size_request(130, -1)
        line.append(date_lbl)

        row.set_child(line)
        self.list.append(row)
        return row

    def clear(self):
        row = self.list.get_first_child()
        while row is not None:
            self.list.remove(row)
            row = self.list.get_first_child()

    def refresh(self):
        self.clear()
        self.build_crumbs()
        self.free.set_text("")

        if self.volume is None:
            for v in self.volumes:
                note = free_space(v.path)
                text = ("voľné " + note + " z " + v.size) if note else v.size
                row = self.add_row(v.name, text, "", None, volume=v)
                self.win.attach_volume_menu(row, v)
            self.win.update_detail()
            return

        space = free_space(self.path)
        if space:
            self.free.set_text("voľné " + space)

        if self.path == self.volume.path:
            custom = self.volume.entries()
            if custom is not None:
                for label, target in custom:
                    self.add_row(label, "", mtime(target), target, is_dir=True, kind="fixed")
                self.win.update_detail()
                return

        if self.path != self.root:
            self.add_row("..", "", "", os.path.dirname(self.path), is_dir=True, kind="parent")

        try:
            items = sorted(
                os.scandir(self.path),
                key=lambda e: (not e.is_dir(), e.name.lower()),
            )
        except (PermissionError, FileNotFoundError):
            self.add_row("Prístup zamietnutý", "", "", None)
            self.win.update_detail()
            return

        for entry in items:
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                self.add_row(entry.name, "", mtime(entry.path), entry.path, is_dir=True)
            else:
                try:
                    size = GLib.format_size(entry.stat().st_size)
                except OSError:
                    size = ""
                self.add_row(entry.name, size, mtime(entry.path), entry.path)
        self.win.update_detail()


# ------------------------------------------------------------------ detail
class Detail(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.set_size_request(260, -1)
        self.set_margin_top(16)
        self.set_margin_bottom(16)
        self.set_margin_start(14)
        self.set_margin_end(14)

        self.icon = Gtk.Image()
        self.icon.set_pixel_size(64)
        self.title = Gtk.Label(wrap=True, justify=Gtk.Justification.CENTER)
        self.title.add_css_class("heading")
        self.rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.append(self.icon)
        self.append(self.title)
        self.append(self.rows)

    def show_path(self, path):
        child = self.rows.get_first_child()
        while child is not None:
            self.rows.remove(child)
            child = self.rows.get_first_child()

        if not path:
            self.icon.set_from_icon_name("folder-symbolic")
            self.title.set_text("Nič nie je vybrané")
            return

        is_dir = os.path.isdir(path)
        self.icon.set_from_icon_name("folder-symbolic" if is_dir else "text-x-generic-symbolic")
        self.title.set_text(os.path.basename(path) or path)

        info = [("Typ", "priečinok" if is_dir else "súbor")]
        if not is_dir:
            try:
                info.append(("Veľkosť", GLib.format_size(os.path.getsize(path))))
            except OSError:
                pass
        info.append(("Zmenené", mtime(path)))

        for key, value in info:
            line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            k = Gtk.Label(label=key, xalign=0, hexpand=True)
            k.add_css_class("dim-label")
            k.add_css_class("detail-key")
            v = Gtk.Label(label=value, xalign=1)
            v.add_css_class("detail-key")
            line.append(k)
            line.append(v)
            self.rows.append(line)


# ------------------------------------------------------------------ okno
class Window(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Súbory")
        self.set_default_size(1200, 720)
        self.volumes = vol_mod.list_volumes()
        self.mode = "simple"        # simple | dual | classic

        header = Gtk.HeaderBar()
        self.set_titlebar(header)

        self.btn_back = Gtk.Button(icon_name="go-previous-symbolic")
        self.btn_back.connect("clicked", lambda _b: self.active.back())
        header.pack_start(self.btn_back)

        self.btn_fwd = Gtk.Button(icon_name="go-next-symbolic")
        self.btn_fwd.connect("clicked", lambda _b: self.active.ahead())
        header.pack_start(self.btn_fwd)

        btn_up = Gtk.Button(icon_name="go-up-symbolic")
        btn_up.connect("clicked", lambda _b: self.active.up())
        header.pack_start(btn_up)

        btn_home = Gtk.Button(icon_name="go-home-symbolic")
        btn_home.connect("clicked", lambda _b: self.active.go_root())
        header.pack_start(btn_home)

        self.view_btn = Gtk.Button(label="Zobrazenie: jednoduché")
        self.view_btn.connect("clicked", self.cycle_mode)
        header.pack_end(self.view_btn)

        # telo
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(body)

        side_scroll = Gtk.ScrolledWindow()
        side_scroll.set_size_request(230, -1)
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
        head_btn.connect("clicked", lambda _b: self.active.go_root())
        side_box.append(head_btn)

        self.side = Gtk.ListBox()
        self.side.connect("row-activated", lambda _b, r: self.active.go_volume(r.volume))
        side_box.append(self.side)
        body.append(side_scroll)
        body.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        body.append(right)

        self.panes = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, hexpand=True, vexpand=True)
        right.append(self.panes)

        self.pane_a = Pane(self, self.volumes)
        self.pane_b = Pane(self, self.volumes)
        self.detail = Detail()
        self.panes.append(self.pane_a)
        self.panes.append(self.pane_b)
        self.panes.append(self.detail)

        right.append(self.function_bar())

        self.active = self.pane_a
        self.fill_sidebar()
        self.apply_mode()

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self.on_key)
        self.add_controller(keys)

    # ---------- bočný panel ----------
    def fill_sidebar(self):
        row = self.side.get_first_child()
        while row is not None:
            self.side.remove(row)
            row = self.side.get_first_child()

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
            self.attach_volume_menu(row, v)
            self.side.append(row)

    def attach_volume_menu(self, widget, volume):
        gesture = Gtk.GestureClick()
        gesture.set_button(3)
        gesture.connect("pressed", lambda *_a, v=volume: self.ask_rename_volume(v))
        widget.add_controller(gesture)

    # ---------- režimy ----------
    def cycle_mode(self, _btn):
        order = ["simple", "dual", "classic"]
        self.mode = order[(order.index(self.mode) + 1) % len(order)]
        self.apply_mode()

    def apply_mode(self):
        labels = {
            "simple": "Zobrazenie: jednoduché",
            "dual": "Zobrazenie: dvojpanel",
            "classic": "Zobrazenie: klasické",
        }
        self.view_btn.set_label(labels[self.mode])
        self.pane_b.set_visible(self.mode != "simple")
        self.detail.set_visible(self.mode == "simple")
        self.pane_a.refresh()
        self.pane_b.refresh()

    def set_active(self, pane):
        self.active = pane
        self.pane_a.remove_css_class("active")
        self.pane_b.remove_css_class("active")
        pane.add_css_class("active")
        self.update_detail()

    def other(self):
        return self.pane_b if self.active is self.pane_a else self.pane_a

    def update_detail(self):
        detail = getattr(self, "detail", None)
        if detail is None or self.mode != "simple":
            return
        active = getattr(self, "active", None)
        detail.show_path(active.selected() if active is not None else None)

    # ---------- spodná lišta ----------
    def function_bar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bar.set_margin_top(6)
        bar.set_margin_bottom(8)
        bar.set_margin_start(8)
        bar.set_margin_end(8)
        items = [
            ("F2 Premenovať", self.do_rename),
            ("F5 Kopírovať", self.do_copy),
            ("F6 Presunúť", self.do_move),
            ("F7 Priečinok", self.do_mkdir),
            ("F8 Do koša", self.do_trash),
        ]
        for label, action in items:
            btn = Gtk.Button(label=label)
            btn.set_hexpand(True)
            btn.connect("clicked", lambda _b, a=action: a())
            bar.append(btn)
        return bar

    # ---------- dialógy ----------
    def ask_text(self, title, initial, on_ok):
        dlg = Gtk.Window(transient_for=self, modal=True, title=title)
        dlg.set_default_size(360, -1)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        for f in (box.set_margin_top, box.set_margin_bottom, box.set_margin_start, box.set_margin_end):
            f(18)
        entry = Gtk.Entry(text=initial)
        box.append(entry)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, halign=Gtk.Align.END)
        cancel = Gtk.Button(label="Zrušiť")
        cancel.connect("clicked", lambda _b: dlg.destroy())
        ok = Gtk.Button(label="Potvrdiť")
        ok.add_css_class("suggested-action")

        def apply(*_a):
            text = entry.get_text().strip()
            dlg.destroy()
            if text:
                on_ok(text)

        ok.connect("clicked", apply)
        entry.connect("activate", apply)
        row.append(cancel)
        row.append(ok)
        box.append(row)
        dlg.set_child(box)
        dlg.present()

    def ask_confirm(self, text, on_ok):
        dlg = Gtk.Window(transient_for=self, modal=True, title="Potvrdenie")
        dlg.set_default_size(380, -1)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        for f in (box.set_margin_top, box.set_margin_bottom, box.set_margin_start, box.set_margin_end):
            f(18)
        label = Gtk.Label(label=text, wrap=True, xalign=0)
        box.append(label)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, halign=Gtk.Align.END)
        cancel = Gtk.Button(label="Zrušiť")
        cancel.connect("clicked", lambda _b: dlg.destroy())
        ok = Gtk.Button(label="Pokračovať")
        ok.add_css_class("destructive-action")
        ok.connect("clicked", lambda _b: (dlg.destroy(), on_ok()))
        row.append(cancel)
        row.append(ok)
        box.append(row)
        dlg.set_child(box)
        dlg.present()

    def notify(self, text):
        dlg = Gtk.AlertDialog()
        dlg.set_message(text)
        dlg.show(self)

    # ---------- operácie ----------
    def open_object(self, path):
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

    def refresh_all(self):
        self.pane_a.refresh()
        self.pane_b.refresh()

    def do_mkdir(self):
        if not self.active.can_write():
            return

        def create(name):
            try:
                os.mkdir(os.path.join(self.active.path, name))
                self.refresh_all()
            except OSError as err:
                self.notify("Priečinok sa nepodarilo vytvoriť: " + err.strerror)

        self.ask_text("Nový priečinok", "", create)

    def do_rename(self):
        src = self.active.selected()
        if not src:
            return

        def rename(name):
            try:
                os.rename(src, os.path.join(os.path.dirname(src), name))
                self.refresh_all()
            except OSError as err:
                self.notify("Premenovanie zlyhalo: " + err.strerror)

        self.ask_text("Premenovať", os.path.basename(src), rename)

    def transfer(self, move):
        src = self.active.selected()
        if not src:
            return
        target_pane = self.other()
        if self.mode == "simple" or not target_pane.can_write():
            self.notify("Cieľ nie je určený. Prepnite na dvojpanel.")
            return
        dst = os.path.join(target_pane.path, os.path.basename(src))
        word = "Presunúť" if move else "Kopírovať"

        def run():
            try:
                if move:
                    shutil.move(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                self.refresh_all()
            except (OSError, shutil.Error) as err:
                self.notify(word + " zlyhalo: " + str(err))

        self.ask_confirm(word + " „" + os.path.basename(src) + "“ do " + target_pane.path + "?", run)

    def do_copy(self):
        self.transfer(False)

    def do_move(self):
        self.transfer(True)

    def do_trash(self):
        src = self.active.selected()
        if not src:
            return

        def run():
            try:
                Gio.File.new_for_path(src).trash(None)
                self.refresh_all()
            except GLib.Error as err:
                self.notify("Do koša sa nepodarilo presunúť: " + err.message)

        self.ask_confirm("Presunúť „" + os.path.basename(src) + "“ do Koša?", run)

    def ask_rename_volume(self, volume):
        def apply(name):
            if vol_mod.rename(volume, name):
                self.fill_sidebar()
                self.refresh_all()

        self.ask_text("Premenovať zväzok", volume.name, apply)

    # ---------- klávesnica ----------
    def on_key(self, _c, keyval, _code, _state):
        if keyval == Gdk.KEY_Tab and self.mode != "simple":
            self.set_active(self.other())
            return True
        if keyval == Gdk.KEY_F2:
            self.do_rename()
            return True
        if keyval == Gdk.KEY_F5:
            self.do_copy()
            return True
        if keyval == Gdk.KEY_F6:
            self.do_move()
            return True
        if keyval == Gdk.KEY_F7:
            self.do_mkdir()
            return True
        if keyval in (Gdk.KEY_F8, Gdk.KEY_Delete):
            self.do_trash()
            return True
        if keyval == Gdk.KEY_BackSpace:
            self.active.up()
            return True
        return False


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.latteos.Files")

    def do_activate(self):
        win = Window(self)
        theme.load(win.get_display())
        win.present()


if __name__ == "__main__":
    App().run(sys.argv)