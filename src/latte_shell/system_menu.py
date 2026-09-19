"""Systémový manažér: popup nad tlačidlom napájania.

Zobrazí sa klikom na tlačidlo a skryje sa, keď kurzor odíde z popupu (alebo Esc,
alebo klik na tlačidlo znova). Ak kurzor do popupu vôbec nevojde, zavrie sa sám.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, Gio, GLib  # noqa: E402
from gi.repository import Gtk4LayerShell as LayerShell  # noqa: E402

from latte_common import build  # noqa: E402
from latte_shell import system  # noqa: E402

WIDTH = 330
WAIT_FOR_POINTER_MS = 2500      # kurzor do popupu nevošiel: zavrieť
LEAVE_DELAY_MS = 250            # krátke vybehnutie z okraja nezavrie


class SystemMenu(Gtk.Window):
    def __init__(self, app, left, bottom, on_closed):
        super().__init__(application=app)
        self.on_closed = on_closed
        self.closed = False
        self.entered = False
        self.leave_source = 0
        self.rows = []
        self.add_css_class("latte-overlay")

        LayerShell.init_for_window(self)
        LayerShell.set_layer(self, LayerShell.Layer.OVERLAY)
        LayerShell.set_anchor(self, LayerShell.Edge.BOTTOM, True)
        LayerShell.set_anchor(self, LayerShell.Edge.LEFT, True)
        LayerShell.set_margin(self, LayerShell.Edge.LEFT, left)
        LayerShell.set_margin(self, LayerShell.Edge.BOTTOM, bottom)
        LayerShell.set_exclusive_zone(self, -1)
        LayerShell.set_keyboard_mode(self, LayerShell.KeyboardMode.ON_DEMAND)
        LayerShell.set_namespace(self, "latte-system-menu")

        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        panel.add_css_class("system-menu")
        panel.set_size_request(WIDTH, -1)
        self.set_child(panel)

        title = Gtk.Label(label="Systémový manažér", xalign=0)
        title.add_css_class("system-title")
        panel.append(title)

        for action in system.ACTIONS:
            panel.append(self.build_row(action))

        self.message = Gtk.Label(xalign=0, wrap=True)
        self.message.add_css_class("system-message")
        self.message.set_visible(False)
        panel.append(self.message)

        foot = Gtk.Box()
        foot.add_css_class("system-foot")
        name = Gtk.Label(label=build.NAME, xalign=0, hexpand=True)
        kind = Gtk.Label(label=build.label(), xalign=1)
        foot.append(name)
        foot.append(kind)
        panel.append(foot)

        motion = Gtk.EventControllerMotion()
        motion.connect("enter", self.on_enter)
        motion.connect("leave", self.on_leave)
        panel.add_controller(motion)

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self.on_key)
        self.add_controller(keys)

        GLib.timeout_add(WAIT_FOR_POINTER_MS, self.on_wait_expired)

    def build_row(self, action):
        button = Gtk.Button()
        button.add_css_class("system-row")
        row = Gtk.Box(spacing=12)
        title = Gtk.Label(label=action.label, xalign=0, hexpand=True)
        hint = Gtk.Label(label=action.hint, xalign=1)
        hint.add_css_class("system-hint")
        row.append(title)
        row.append(hint)
        button.set_child(row)
        button.connect("clicked", lambda _b, a=action: self.run(a))
        self.rows.append(button)
        return button

    # ---------- skrývanie ----------
    def on_enter(self, *_args):
        self.entered = True
        if self.leave_source:
            GLib.source_remove(self.leave_source)
            self.leave_source = 0

    def on_leave(self, *_args):
        if self.entered and not self.leave_source:
            self.leave_source = GLib.timeout_add(LEAVE_DELAY_MS, self.close_from_timer)

    def on_wait_expired(self):
        if not self.entered:
            self.close_menu()
        return False

    def close_from_timer(self):
        self.leave_source = 0
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
        if self.leave_source:
            GLib.source_remove(self.leave_source)
            self.leave_source = 0
        self.on_closed()
        self.destroy()

    # ---------- akcie ----------
    def show_message(self, text):
        self.message.set_text(text)
        self.message.set_visible(bool(text))

    def set_rows_sensitive(self, sensitive):
        for row in self.rows:
            row.set_sensitive(sensitive)

    def run(self, action):
        greetd = system.greetd_active() if action.id == "console" else False
        if greetd and not system.console_permitted():
            # Bez pravidla by sa po odhlásení ukázalo prihlasovanie a nie konzola.
            self.show_message(
                "Vypnúť do konzoly potrebuje pravidlo polkit: spusti tools/install-greeter.sh ako root"
            )
            return
        argv = system.command(action.id, greetd)
        reason = system.unavailable_reason(argv)
        if reason:
            self.show_message("%s sa nedá: %s" % (action.label, reason))
            return
        self.set_rows_sensitive(False)
        self.show_message(action.label + "…")
        try:
            proc = Gio.Subprocess.new(argv, Gio.SubprocessFlags.STDERR_PIPE)
        except GLib.Error as err:
            self.fail(action, err.message)
            return
        proc.communicate_utf8_async(None, None, self.on_finished, (action, proc))

    def on_finished(self, proc, result, data):
        action, _proc = data
        try:
            _ok, _out, err = proc.communicate_utf8_finish(result)
        except GLib.Error as error:
            self.fail(action, error.message)
            return
        if proc.get_exit_status() != 0:
            self.fail(action, (err or "").strip() or "kód %d" % proc.get_exit_status())
        # Pri úspechu relácia skončí a s ňou aj lišta; popup zostane, kým to nenastane.

    def fail(self, action, text):
        if self.closed:
            return
        self.set_rows_sensitive(True)
        self.show_message("%s zlyhalo: %s" % (action.label, text))
