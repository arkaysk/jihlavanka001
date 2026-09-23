"""Popup nad lištou, ktorý sa skryje, keď z neho kurzor odíde (systémový manažér, manažér času).

Zatvorí sa aj Esc, kliknutím na tlačidlo, ktoré ho otvorilo (rieši lišta), alebo sám, ak kurzor
do popupu vôbec nevojde. Kým podtrieda hlási holding() (napr. píše sa do políčka), neskryje sa.
"""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402
from gi.repository import Gtk4LayerShell as LayerShell  # noqa: E402

WAIT_FOR_POINTER_MS = 2500      # kurzor do popupu nevošiel: zavrieť
LEAVE_DELAY_MS = 250            # krátke vybehnutie z okraja nezavrie


class HoverPopup(Gtk.Window):
    def __init__(self, app, left, bottom, namespace, on_closed):
        super().__init__(application=app)
        self.on_closed = on_closed
        self.closed = False
        self.entered = False
        self.leave_source = 0
        self.wait_source = 0
        self.add_css_class("latte-overlay")

        LayerShell.init_for_window(self)
        LayerShell.set_layer(self, LayerShell.Layer.OVERLAY)
        LayerShell.set_anchor(self, LayerShell.Edge.BOTTOM, True)
        LayerShell.set_anchor(self, LayerShell.Edge.LEFT, True)
        LayerShell.set_margin(self, LayerShell.Edge.LEFT, left)
        LayerShell.set_margin(self, LayerShell.Edge.BOTTOM, bottom)
        LayerShell.set_exclusive_zone(self, -1)
        LayerShell.set_keyboard_mode(self, LayerShell.KeyboardMode.ON_DEMAND)
        LayerShell.set_namespace(self, namespace)

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self.on_key)
        self.add_controller(keys)

    def set_panel(self, panel):
        self.set_child(panel)
        motion = Gtk.EventControllerMotion()
        motion.connect("enter", self.on_enter)
        motion.connect("leave", self.on_leave)
        panel.add_controller(motion)
        self.wait_source = GLib.timeout_add(WAIT_FOR_POINTER_MS, self.on_wait_expired)

    def holding(self):
        """True, kým sa popup nesmie sám zavrieť."""
        return False

    def on_enter(self, *_args):
        self.entered = True
        if self.leave_source:
            GLib.source_remove(self.leave_source)
            self.leave_source = 0

    def on_leave(self, *_args):
        if self.entered and not self.leave_source:
            self.leave_source = GLib.timeout_add(LEAVE_DELAY_MS, self.close_from_timer)

    def on_wait_expired(self):
        self.wait_source = 0
        if not self.entered and not self.holding():
            self.close_menu()
        return False

    def close_from_timer(self):
        self.leave_source = 0
        if not self.holding():
            self.close_menu()
        return False

    def on_key(self, _ctrl, keyval, _code, _state):
        if keyval == Gdk.KEY_Escape:
            self.close_menu()
            return True
        return False

    def close_menu(self):
        if self.closed:
            return
        self.closed = True
        for source in (self.leave_source, self.wait_source):
            if source:
                GLib.source_remove(source)
        self.leave_source = self.wait_source = 0
        self.on_closed()
        self.destroy()
