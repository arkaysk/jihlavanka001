"""Prompt v lište (bod 2.8): jedno políčko a malá prepínacia ikona vľavo.

Ikona prepína režim: lupa (hľadať v priečinkoch), znak konzoly Linuxu (príkazy) a AI (LM Studio).
Výsledky, výstup a rozhovor sa ukazujú v popupe nad lištou; režimy sú v prompt_modes.py.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, Pango  # noqa: E402
from gi.repository import Gtk4LayerShell as LayerShell  # noqa: E402

from latte_common import paths, prefs  # noqa: E402
from latte_shell.prompt_modes import MODE_CLASSES, tool_button  # noqa: E402

PROMPT_WIDTH = 420                # najmenšia šírka; inak sa lišta delí so zoznamom okien
POPUP_MIN_WIDTH = 640
POPUP_GAP = 6                   # medzera nad lištou
BAR_HEIGHT = 104


def register_icons(display):
    """Vlastné ikony LatteOS (data/icons) popri systémovej téme."""
    Gtk.IconTheme.get_for_display(display).add_search_path(os.path.join(paths.data_dir(), "icons"))


class PromptPopup(Gtk.Window):
    """Panel nad lištou, zarovnaný s políčkom promptu. Kláves nedostáva, píše sa do políčka."""

    def __init__(self, app, left, width, on_closed):
        super().__init__(application=app)
        self.on_closed = on_closed
        self.closed = False
        self.mode = None
        self.add_css_class("latte-overlay")

        LayerShell.init_for_window(self)
        LayerShell.set_layer(self, LayerShell.Layer.TOP)
        LayerShell.set_anchor(self, LayerShell.Edge.BOTTOM, True)
        LayerShell.set_anchor(self, LayerShell.Edge.LEFT, True)
        LayerShell.set_margin(self, LayerShell.Edge.LEFT, left)
        LayerShell.set_margin(self, LayerShell.Edge.BOTTOM, BAR_HEIGHT + POPUP_GAP)
        LayerShell.set_exclusive_zone(self, -1)
        LayerShell.set_keyboard_mode(self, LayerShell.KeyboardMode.NONE)
        LayerShell.set_namespace(self, "latte-prompt")

        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        panel.add_css_class("prompt-popup")
        panel.set_size_request(width, -1)
        self.set_child(panel)

        head = Gtk.Box(spacing=8)
        head.add_css_class("prompt-head")
        self.icon = Gtk.Image()
        self.icon.set_pixel_size(16)
        self.title = Gtk.Label(xalign=0, hexpand=True)
        self.title.set_ellipsize(Pango.EllipsizeMode.END)
        self.title.add_css_class("prompt-title")
        self.extras = Gtk.Box(spacing=2)
        head.append(self.icon)
        head.append(self.title)
        head.append(self.extras)
        self.close_button = tool_button("window-close-symbolic", "Zavrieť (Esc)", self.close_popup)
        head.append(self.close_button)
        panel.append(head)

        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        panel.append(self.body)

    def set_mode(self, mode):
        if self.mode is not None:
            self.body.remove(self.mode.view)
            for button in self.mode.extras():
                self.extras.remove(button)
        self.mode = mode
        self.icon.set_from_icon_name(mode.icon)
        self.body.append(mode.view)
        for button in mode.extras():
            self.extras.append(button)
        self.update_title()

    def update_title(self):
        if self.mode is not None:
            self.title.set_text(self.mode.title())

    def close_popup(self):
        if self.closed:
            return
        self.closed = True
        if self.mode is not None:            # zobrazenie prežije, zatvára sa len okno
            self.body.remove(self.mode.view)
            for button in self.mode.extras():
                self.extras.remove(button)
            self.mode = None
        self.on_closed()
        self.destroy()


class PromptSegment(Gtk.Box):
    def __init__(self, open_files):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.open_files_callback = open_files
        self.popup = None
        self.add_css_class("segment")
        self.add_css_class("prompt-segment")
        self.set_size_request(PROMPT_WIDTH, 64)
        self.set_hexpand(True)
        self.set_valign(Gtk.Align.CENTER)

        self.modes = [cls(self) for cls in MODE_CLASSES]
        self.mode = self.modes[0]

        self.mode_button = Gtk.Button()
        self.mode_button.add_css_class("prompt-mode")
        self.mode_button.set_valign(Gtk.Align.CENTER)
        self.mode_button.set_size_request(38, 38)
        self.mode_image = Gtk.Image()
        self.mode_image.set_pixel_size(18)
        self.mode_button.set_child(self.mode_image)
        self.mode_button.connect("clicked", lambda _b: self.cycle(1))
        scroll = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.VERTICAL)
        scroll.connect("scroll", self.on_scroll)
        self.mode_button.add_controller(scroll)
        self.append(self.mode_button)

        self.prefix = Gtk.Label()
        self.prefix.add_css_class("prompt-prefix")
        self.prefix.set_max_width_chars(14)
        self.prefix.set_ellipsize(Pango.EllipsizeMode.START)
        self.append(self.prefix)

        self.entry = Gtk.Entry(hexpand=True)
        self.entry.set_has_frame(False)
        self.entry.add_css_class("prompt-entry")
        self.entry.set_valign(Gtk.Align.CENTER)
        self.entry.connect("changed", lambda e: self.mode.changed(e.get_text()))
        self.entry.connect("activate", lambda e: self.mode.submit(e.get_text()))
        keys = Gtk.EventControllerKey()
        keys.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", self.on_key)
        self.entry.add_controller(keys)
        self.append(self.entry)

        saved = prefs.load("prompt").get("mode", "")
        start = next((i for i, m in enumerate(self.modes) if m.id == saved), 0)
        self.set_mode(start, save=False)

    # ---------- režimy ----------
    def set_mode(self, index, save=True):
        self.mode = self.modes[index % len(self.modes)]
        mode = self.mode
        self.mode_image.set_from_icon_name(mode.icon)
        self.mode_button.set_tooltip_text(
            "%s\nKlik alebo Ctrl+1/2/3 prepne režim: hľadať, terminál, AI" % mode.name)
        self.entry.set_placeholder_text(mode.placeholder)
        for m in self.modes:
            (self.add_css_class if m is mode else self.remove_css_class)("mode-" + m.id)
        self.prefix.set_visible(mode.id == "terminal")
        mode.activated()
        if self.popup is not None:
            self.popup.set_mode(mode)
        if mode.id == "search" and self.entry.get_text():
            mode.changed(self.entry.get_text())
        if save:
            try:
                prefs.update("prompt", mode=mode.id)
            except OSError as err:
                print("latte-shell: režim promptu sa nepodarilo uložiť:", err, file=sys.stderr)

    def cycle(self, step):
        self.set_mode(self.modes.index(self.mode) + step)
        self.entry.grab_focus()

    def on_scroll(self, _ctrl, _dx, dy):
        self.cycle(1 if dy > 0 else -1)
        return True

    def on_key(self, _ctrl, keyval, _code, state):
        ctrl = state & Gdk.ModifierType.CONTROL_MASK
        if keyval == Gdk.KEY_Escape:
            if self.popup is not None:
                self.close_popup()
            else:
                self.entry.set_text("")
                self.get_root().set_focus(None)
            return True
        if ctrl and Gdk.KEY_1 <= keyval <= Gdk.KEY_3:
            self.set_mode(keyval - Gdk.KEY_1)
            return True
        if ctrl and keyval in (Gdk.KEY_c, Gdk.KEY_C) and self.entry.get_selection_bounds():
            return False                        # kopírovanie označeného textu
        return self.mode.key(keyval, state)

    # ---------- rozhranie pre režimy ----------
    def show(self, mode):
        if self.popup is None:
            found, rect = self.compute_bounds(self.get_root())
            left = int(rect.get_x()) if found else 12
            width = max(int(rect.get_width()) if found else PROMPT_WIDTH, POPUP_MIN_WIDTH)
            self.popup = PromptPopup(self.get_root().get_application(), left, width, self.popup_closed)
            self.popup.set_mode(mode)
            self.popup.present()
        elif self.popup.mode is not mode:
            self.popup.set_mode(mode)

    def refresh(self):
        if self.popup is not None:
            self.popup.update_title()

    def close_popup(self):
        if self.popup is not None:
            self.popup.close_popup()

    def popup_closed(self):
        self.popup = None

    def set_entry_text(self, text):
        self.entry.set_text(text)
        self.entry.set_position(-1)

    def set_prefix(self, text):
        self.prefix.set_text(text + " $")

    def open_files(self, path):
        self.open_files_callback(path)
