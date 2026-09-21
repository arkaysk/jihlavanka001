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

from latte_common import appearance, scenes, settings, theme, wallpaper, widgets  # noqa: E402
from latte_shell import bar_texture, maps  # noqa: E402
from latte_shell.desktop_icons import DesktopIcons, MARGIN  # noqa: E402
from latte_shell import geometry  # noqa: E402
from latte_shell import notify_center, notify_service  # noqa: E402
from latte_shell.prompt import PromptSegment, register_icons  # noqa: E402
from latte_shell.system_menu import SystemMenu  # noqa: E402
from latte_shell.tasks import TaskList  # noqa: E402
from latte_shell.time_menu import TimeMenu  # noqa: E402
from latte_shell.time_segment import TimeSegment  # noqa: E402
from latte_shell.toasts import ToastStack  # noqa: E402

FILES_APP = os.path.join(os.path.dirname(__file__), "..", "latte_files", "app.py")
SETTINGS_APP = os.path.join(os.path.dirname(__file__), "..", "latte_settings", "app.py")
PROCESS_MANAGER_APP = os.path.join(os.path.dirname(__file__), "..", "latte_process", "app.py")
DEVICES_APP = os.path.join(os.path.dirname(__file__), "..", "latte_devices", "app.py")


class Desktop(Gtk.ApplicationWindow):
    """Tapeta plochy: vrstva BACKGROUND pod všetkými oknami.

    Berie tapetu z latte_common.wallpaper (používateľská, inak systémová)
    a mení ju hneď, ako sa zmení ~/.config/latteos/appearance.toml.
    Nad tapetou sú ikony plochy (desktop_icons.py). Zatiaľ len na predvolenom monitore.
    """

    def __init__(self, app, open_files):
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
        overlay = Gtk.Overlay()
        overlay.set_child(self.picture)
        self.icons = DesktopIcons(open_files)
        self.icons.set_margin_top(MARGIN)
        self.icons.set_margin_start(MARGIN)
        self.set_bar_height()
        overlay.add_overlay(self.icons)
        self.set_child(overlay)
        self.reload()

        # Sleduje sa adresár, nie súbor: appearance.toml sa zapisuje cez premenovanie
        # a nemusí ešte existovať.
        os.makedirs(os.path.dirname(wallpaper.appearance_file()), exist_ok=True)
        self.monitor = Gio.File.new_for_path(
            os.path.dirname(wallpaper.appearance_file())
        ).monitor_directory(Gio.FileMonitorFlags.WATCH_MOVES, None)
        self.monitor.connect("changed", self.on_config_changed)

    def set_bar_height(self):
        """Ikony plochy končia nad lištou (plocha siaha aj pod ňu)."""
        self.icons.set_margin_bottom(geometry.bar_height() + MARGIN)

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
        self.time_menu = None
        self.tiles = {}                 # rohové dlaždice podľa druhu (kým je popup otvorený, majú triedu open)

        LayerShell.init_for_window(self)
        LayerShell.set_layer(self, LayerShell.Layer.TOP)
        LayerShell.set_anchor(self, LayerShell.Edge.BOTTOM, True)
        LayerShell.set_anchor(self, LayerShell.Edge.LEFT, True)
        LayerShell.set_anchor(self, LayerShell.Edge.RIGHT, True)
        LayerShell.set_exclusive_zone(self, geometry.bar_height())
        # políčko promptu dostane kláves po kliknutí (bez toho by lišta klávesnicu nedostala)
        LayerShell.set_keyboard_mode(self, LayerShell.KeyboardMode.ON_DEMAND)
        LayerShell.set_namespace(self, "latte-shell")

        # všetky dlaždice (rohy aj segmenty) sú pritlačené k spodnému okraju obrazovky
        # a majú hornú hranu v rovnakej výške; medzi nimi je len vodorovná medzera
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(row)

        middle = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, hexpand=True)
        middle.set_margin_start(8)
        middle.set_margin_end(8)

        row.append(self.corner_tile("apps", False))
        row.append(middle)
        row.append(self.corner_tile("resources", True))

        self.clock_segment = TimeSegment(app.center, self.toggle_time_menu)
        middle.append(self.clock_segment)
        middle.append(self.system_segment())

        middle.append(TaskList())
        middle.append(PromptSegment(self.launch_files))

        middle.append(self.files_segment())

    def apply_height(self):
        """Výška lišty sa zmenila: rezervované miesto pre okná a rohové dlaždice. Otvorené popupy sa
        zatvoria, lebo majú starú polohu."""
        self.close_menus()
        LayerShell.set_exclusive_zone(self, geometry.bar_height())
        for tile in self.tiles.values():
            tile.set_size_request(geometry.corner_width(), geometry.bar_height())
            tile.icon.set_pixel_size(geometry.corner_icon_size())
        self.queue_resize()

    # ---------- segmenty ----------
    def corner_tile(self, kind, right):
        """Rohová dlaždica: len ikona nad textúrou, ako ostatné položky lišty. Názov je v tooltipe a pre čítačky
        obrazovky; celý sa ukáže až v otvorenom popupe (maps.NAMES)."""
        btn = Gtk.Button()
        btn.add_css_class("corner")
        if right:
            btn.add_css_class("right")
        self.tiles[kind] = btn
        btn.kind, btn.right = kind, right
        btn.set_tooltip_text(maps.NAMES[kind])
        btn.update_property([Gtk.AccessibleProperty.LABEL], [maps.NAMES[kind]])
        btn.set_size_request(geometry.corner_width(), geometry.bar_height())
        btn.set_hexpand(False)          # dlaždica má presný rozmer, o voľné miesto sa delí len stred lišty
        btn.set_overflow(Gtk.Overflow.HIDDEN)           # textúra sa orezáva podľa zaoblenia dlaždice
        hover = Gtk.EventControllerMotion()             # režim pohybu „len pod kurzorom“
        hover.connect("enter", lambda *_a: self.hover_tile(kind, True))
        hover.connect("leave", lambda *_a: self.hover_tile(kind, False))
        btn.add_controller(hover)
        btn.connect("clicked", lambda _b, k=kind: self.toggle_popup(k))
        self.fill_tile(btn)
        return btn

    def fill_tile(self, btn):
        """Obsah rohovej dlaždice: textúra (ak ju má) pod ikonou. Volá sa aj po zmene nastavení."""
        icon = Gtk.Image.new_from_icon_name("drive-harddisk-symbolic" if btn.right else "view-grid-symbolic")
        icon.set_pixel_size(geometry.corner_icon_size())
        icon.set_halign(Gtk.Align.CENTER)
        icon.set_valign(Gtk.Align.CENTER)
        btn.icon = icon
        inner = icon
        texture = self.get_application().textures.get(btn.kind)
        if texture is None:
            btn.set_child(inner)
            return
        stack = Gtk.Overlay()
        stack.set_child(texture.view(lambda: bar_texture.corner_rect(btn.right), btn.right))
        stack.add_overlay(inner)
        btn.set_child(stack)

    def fill_tiles(self):
        for btn in self.tiles.values():
            self.fill_tile(btn)

    def hover_tile(self, kind, flag):
        texture = self.get_application().textures.get(kind)
        if texture is not None:
            texture.set_hovered(flag)

    def icon_segment(self, icon_name, action):
        btn = Gtk.Button()
        btn.add_css_class("segment")
        btn.set_size_request(geometry.ICON_SEGMENT_WIDTH, -1)
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
    def launch_files(self, path=None):
        """Správca súborov, prípadne rovno v priečinku `path`."""
        argv = [sys.executable, os.path.abspath(FILES_APP)]
        if path:
            argv.append(path)
        subprocess.Popen(argv)

    def launch_settings(self, target=None):
        """Nastavenia systému, prípadne rovno na stránke (settings://oblasť/stránka)."""
        argv = [sys.executable, os.path.abspath(SETTINGS_APP)]
        if target:
            argv.append(target)
        subprocess.Popen(argv)

    def launch_details(self, kind):
        """Tlačidlo do podrobností v otvorenom popupe. App Manager ešte nie je (etapa 4): vedie na stránku
        Inštalácia aplikácií v Nastaveniach, ktorá to povie a neskôr ho otvorí. Zariadenia: Správca zariadení."""
        if kind == "apps":
            self.launch_settings("settings://software/install")
        else:
            subprocess.Popen([sys.executable, os.path.abspath(DEVICES_APP)])

    def launch_app(self, info):
        try:
            info.launch([], None)
        except GLib.Error:
            pass
        if self.popup is not None:
            self.popup.close_popup()

    def close_menus(self):
        """Naraz je otvorený najviac jeden popup nad lištou."""
        if self.system_menu is not None:
            self.system_menu.close_menu()
        if self.time_menu is not None:
            self.time_menu.close_menu()
        if self.popup is not None:
            self.popup.close_popup()

    def toggle_time_menu(self, page):
        if self.time_menu is not None:
            if self.time_menu.page == page:
                self.time_menu.close_menu()
            else:
                self.time_menu.show_page(page)
            return
        self.close_menus()
        found, rect = self.clock_segment.compute_bounds(self)
        left = int(rect.get_x()) if found else 12
        app = self.get_application()
        self.time_menu = TimeMenu(app, left, geometry.bar_height() + 6, self.time_menu_closed,
                                  app.center, app.notify_service, page)
        self.time_menu.present()

    def time_menu_closed(self):
        self.time_menu = None

    def toggle_system_menu(self):
        if self.system_menu is not None:
            self.system_menu.close_menu()
            return
        self.close_menus()
        # popup začína nad hodinami a siaha nad tlačidlo napájania
        found, rect = self.clock_segment.compute_bounds(self)
        left = int(rect.get_x()) if found else 12
        self.system_menu = SystemMenu(
            self.get_application(), left, geometry.bar_height() + 6, self.system_menu_closed,
            self.launch_settings, self.launch_process_manager
        )
        self.system_menu.present()

    def system_menu_closed(self):
        self.system_menu = None

    def launch_process_manager(self):
        subprocess.Popen([sys.executable, os.path.abspath(PROCESS_MANAGER_APP)])

    def toggle_popup(self, kind):
        if self.system_menu is not None:
            self.system_menu.close_menu()
        if self.time_menu is not None:
            self.time_menu.close_menu()
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
        self.popup = maps.MapOverlay(app, kind, self.launch_app, self.popup_closed, self.launch_settings,
                                     self.launch_details)
        self.tiles[kind].add_css_class("open")
        self.popup.present()

    def popup_closed(self):
        if self.popup is not None:
            self.tiles[self.popup.kind].remove_css_class("open")
        self.popup = None


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.latteos.Shell")
        self.map_windows = {}
        self.bar = None
        self.textures = {}              # textúry rohových dlaždíc podľa druhu (bar_texture.build)
        self.center = notify_center.Center()
        self.notify_service = notify_service.Service(self.center)
        self.toasts = None
        self.desktop = None
        self.appearance = None          # nastavenia vzhľadu (výška lišty, textúry rohov)
        self.appearance_watch = None
        self.bars_config = None         # bar_texture.Config, podľa ktorej sú postavené textúry

    def load_bar_height(self):
        """Výška lišty z nastavení; zmena súboru sa prejaví hneď (bar.height v appearance.toml)."""
        self.appearance = settings.Registry().store("appearance")
        geometry.set_bar_height(self.appearance.get("bar.height"))
        self.load_textures()
        self.appearance_watch = settings.watch([self.appearance.domain.file], self.on_appearance_changed)

    def load_textures(self):
        """Textúry rohov z nastavení (oddiel bars) a farieb motívu. Vráti True, ak sa niečo zmenilo."""
        palette = scenes.palette_from_colors(appearance.current_tokens(self.appearance).colors)
        config = bar_texture.Config.from_values(self.appearance.values(), palette)
        if config == self.bars_config:
            return False
        self.bars_config = config
        self.textures = bar_texture.build(config)
        return True

    def on_appearance_changed(self):
        self.appearance.reload()
        height_changed = geometry.set_bar_height(self.appearance.get("bar.height"))
        if self.bar is None:
            return
        if height_changed:
            for texture in self.textures.values():
                texture.set_bar_height()
        textures_changed = self.load_textures()             # po zmene výšky, aby ju nové plátna mali správnu
        if height_changed or textures_changed:
            self.bar.apply_height()
            if textures_changed:
                self.bar.fill_tiles()
            self.desktop.set_bar_height()

    def launch_settings(self, target=None):
        if self.bar is not None:
            self.bar.launch_settings(target)

    def launch_details(self, kind):
        if self.bar is not None:
            self.bar.launch_details(kind)

    def register_map_window(self, kind, win):
        self.map_windows[kind] = win

    def map_window_closed(self, kind):
        self.map_windows.pop(kind, None)

    def do_activate(self):
        if self.bar is not None:
            return                      # druhé spustenie nevyrobí druhú lištu
        self.load_bar_height()
        bar = self.bar = Bar(self)
        theme.load(bar.get_display())
        register_icons(bar.get_display())
        self.toasts = ToastStack(self, self.center)
        self.notify_service.own_name()
        self.desktop = Desktop(self, bar.launch_files)
        self.desktop.present()
        bar.present()


if __name__ == "__main__":
    App().run(sys.argv)