#!/usr/bin/env python3
"""latte-shell: lišta LatteOS."""
import os
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, GLib  # noqa: E402
from gi.repository import Gtk4LayerShell as LayerShell  # noqa: E402

from latte_common import theme  # noqa: E402
from latte_shell import maps  # noqa: E402
from latte_shell.tasks import TaskList  # noqa: E402

BAR_HEIGHT = 104
CORNER = 104
FILES_APP = os.path.join(os.path.dirname(__file__), "..", "latte_files", "app.py")


class Bar(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.add_css_class("latte-bar")
        self.popup = None

        LayerShell.init_for_window(self)
        LayerShell.set_layer(self, LayerShell.Layer.TOP)
        LayerShell.set_anchor(self, LayerShell.Edge.BOTTOM, True)
        LayerShell.set_anchor(self, LayerShell.Edge.LEFT, True)
        LayerShell.set_anchor(self, LayerShell.Edge.RIGHT, True)
        LayerShell.set_exclusive_zone(self, BAR_HEIGHT)
        LayerShell.set_namespace(self, "latte-shell")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.set_margin_start(12)
        row.set_margin_end(12)
        row.set_margin_bottom(10)
        row.set_margin_top(8)
        self.set_child(row)

        row.append(self.corner_tile("APP MANAGER", "apps", False))
        row.append(self.time_segment())
        row.append(self.system_segment())

        row.append(TaskList())

        row.append(self.files_segment())
        row.append(self.corner_tile("ZDROJE", "resources", True))

        GLib.timeout_add_seconds(10, self.tick)

    # ---------- segmenty ----------
    def corner_tile(self, label, kind, right):
        btn = Gtk.Button()
        btn.add_css_class("corner")
        if right:
            btn.add_css_class("right")
        btn.set_size_request(CORNER, 96)
        btn.set_valign(Gtk.Align.END)

        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        inner.set_valign(Gtk.Align.CENTER)
        icon = Gtk.Image.new_from_icon_name(
            "drive-harddisk-symbolic" if right else "view-grid-symbolic"
        )
        icon.set_pixel_size(32)
        text = Gtk.Label(label=label)
        text.add_css_class("corner-label")
        inner.append(icon)
        inner.append(text)
        btn.set_child(inner)
        btn.connect("clicked", lambda _b, k=kind: self.toggle_popup(k))
        return btn

    def time_segment(self):
        btn = Gtk.Button()
        btn.add_css_class("segment")
        btn.set_size_request(200, 64)
        btn.set_valign(Gtk.Align.CENTER)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_halign(Gtk.Align.CENTER)
        self.clock = Gtk.Label()
        self.clock.add_css_class("clock")
        self.date = Gtk.Label()
        self.date.add_css_class("dim")
        box.append(self.clock)
        box.append(self.date)
        btn.set_child(box)
        self.tick()
        return btn

    def icon_segment(self, icon_name, action):
        btn = Gtk.Button()
        btn.add_css_class("segment")
        btn.set_size_request(64, 64)
        btn.set_valign(Gtk.Align.CENTER)
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(24)
        btn.set_child(icon)
        btn.connect("clicked", action)
        return btn

    def system_segment(self):
        return self.icon_segment("system-shutdown-symbolic", lambda _b: None)

    def files_segment(self):
        return self.icon_segment("folder-symbolic", lambda _b: self.launch_files())

    # ---------- akcie ----------
    def tick(self, *_a):
        now = datetime.now()
        self.clock.set_text(now.strftime("%H:%M"))
        self.date.set_text(now.strftime("%-d. %-m. %Y"))
        return True

    def launch_files(self):
        subprocess.Popen([sys.executable, os.path.abspath(FILES_APP)])

    def launch_app(self, info):
        try:
            info.launch([], None)
        except GLib.Error:
            pass
        if self.popup is not None:
            self.popup.close_popup()

    def toggle_popup(self, kind):
        app = self.get_application()
        win = app.map_windows.get(kind)
        if win is not None:
            win.present()          # už je pripnuté: vyzdvihni okno
            return
        if self.popup is not None:
            same = self.popup.kind == kind
            self.popup.close_popup()
            if same:
                return
        self.popup = maps.MapOverlay(app, kind, self.launch_app, self.popup_closed)
        self.popup.present()

    def popup_closed(self):
        self.popup = None


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.latteos.Shell")
        self.map_windows = {}

    def register_map_window(self, kind, win):
        self.map_windows[kind] = win

    def map_window_closed(self, kind):
        self.map_windows.pop(kind, None)

    def do_activate(self):
        bar = Bar(self)
        theme.load(bar.get_display())
        bar.present()


if __name__ == "__main__":
    App().run(sys.argv)