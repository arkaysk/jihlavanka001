#!/usr/bin/env python3
"""latte-shell: lišta LatteOS."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gio, GLib  # noqa: E402
from gi.repository import Gtk4LayerShell as LayerShell  # noqa: E402

from latte_common import theme, wallpaper, widgets  # noqa: E402
from latte_shell import maps  # noqa: E402
from latte_shell.system_menu import SystemMenu  # noqa: E402
from latte_shell.tasks import TaskList  # noqa: E402

BAR_HEIGHT = 104
CORNER = 104
FILES_APP = os.path.join(os.path.dirname(__file__), "..", "latte_files", "app.py")


class Desktop(Gtk.ApplicationWindow):
    """Tapeta plochy: vrstva BACKGROUND pod všetkými oknami.

    Berie tapetu z latte_common.wallpaper (používateľská, inak systémová)
    a mení ju hneď, ako sa zmení ~/.config/latteos/appearance.toml.
    Zatiaľ len na predvolenom monitore.
    """

    def __init__(self, app):
        super().__init__(application=app)
        self.add_css_class("latte-desktop")
        self.reload_source = 0

        LayerShell.init_for_window(self)
        LayerShell.set_layer(self, LayerShell.Layer.BACKGROUND)
        for edge in (LayerShell.Edge.TOP, LayerShell.Edge.BOTTOM,
                     LayerShell.Edge.LEFT, LayerShell.Edge.RIGHT):
            LayerShell.set_anchor(self, edge, True)
        LayerShell.set_exclusive_zone(self, -1)      # ignoruje rezervované miesto lišty
        LayerShell.set_keyboard_mode(self, LayerShell.KeyboardMode.NONE)
        LayerShell.set_namespace(self, "latte-wallpaper")

        self.picture = widgets.Wallpaper()
        self.set_child(self.picture)
        self.reload()

        # Sleduje sa adresár, nie súbor: appearance.toml sa zapisuje cez premenovanie
        # a nemusí ešte existovať.
        os.makedirs(os.path.dirname(wallpaper.appearance_file()), exist_ok=True)
        self.monitor = Gio.File.new_for_path(
            os.path.dirname(wallpaper.appearance_file())
        ).monitor_directory(Gio.FileMonitorFlags.WATCH_MOVES, None)
        self.monitor.connect("changed", self.on_config_changed)

    def on_config_changed(self, _monitor, file, other, _event):
        name = os.path.basename(wallpaper.appearance_file())
        touched = {file.get_basename(), other.get_basename() if other else None}
        if name in touched and not self.reload_source:
            self.reload_source = GLib.timeout_add(150, self.reload)

    def reload(self):
        self.reload_source = 0
        self.picture.set_path(wallpaper.desktop_path(), wallpaper.desktop_fit())
        return False


class Bar(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.add_css_class("latte-bar")
        self.popup = None
        self.system_menu = None

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
        self.clock_segment = widgets.ClockSegment()
        row.append(self.clock_segment)
        row.append(self.system_segment())

        row.append(TaskList())

        row.append(self.files_segment())
        row.append(self.corner_tile("ZDROJE", "resources", True))

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
        return self.icon_segment("system-shutdown-symbolic", lambda _b: self.toggle_system_menu())

    def files_segment(self):
        return self.icon_segment("folder-symbolic", lambda _b: self.launch_files())

    # ---------- akcie ----------
    def launch_files(self):
        subprocess.Popen([sys.executable, os.path.abspath(FILES_APP)])

    def launch_app(self, info):
        try:
            info.launch([], None)
        except GLib.Error:
            pass
        if self.popup is not None:
            self.popup.close_popup()

    def toggle_system_menu(self):
        if self.system_menu is not None:
            self.system_menu.close_menu()
            return
        if self.popup is not None:
            self.popup.close_popup()
        # popup začína nad hodinami a siaha nad tlačidlo napájania
        found, rect = self.clock_segment.compute_bounds(self)
        left = int(rect.get_x()) if found else 12
        self.system_menu = SystemMenu(
            self.get_application(), left, BAR_HEIGHT + 6, self.system_menu_closed
        )
        self.system_menu.present()

    def system_menu_closed(self):
        self.system_menu = None

    def toggle_popup(self, kind):
        if self.system_menu is not None:
            self.system_menu.close_menu()
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
        Desktop(self).present()
        bar.present()


if __name__ == "__main__":
    App().run(sys.argv)