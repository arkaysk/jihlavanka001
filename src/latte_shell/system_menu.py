"""Systémový manažér: popup nad tlačidlom napájania.

Zobrazí sa klikom na tlačidlo a skryje sa, keď kurzor odíde z popupu (alebo Esc,
alebo klik na tlačidlo znova). Ak kurzor do popupu vôbec nevojde, zavrie sa sám.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib  # noqa: E402

from latte_common import build  # noqa: E402
from latte_shell import system  # noqa: E402
from latte_shell.popup import HoverPopup  # noqa: E402

WIDTH = 330
CONFIRM_MS = 4000               # koľko čaká potvrdenie akcie s confirm


class SystemMenu(HoverPopup):
    def __init__(self, app, left, bottom, on_closed, on_settings):
        super().__init__(app, left, bottom, "latte-system-menu", on_closed)
        self.confirming = None      # (akcia, tlačidlo, zdroj časovača)
        self.rows = []
        self.on_settings = on_settings

        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        panel.add_css_class("system-menu")
        panel.set_size_request(WIDTH, -1)

        title = Gtk.Label(label="Systémový manažér", xalign=0)
        title.add_css_class("system-title")
        panel.append(title)

        # Nastavenia idú pred napájanie: nie sú to akcie, ktoré končia reláciu, preto ani potvrdenie,
        # ani zablokovanie pri behu vypnutia (nie sú v self.rows)
        panel.append(self.settings_row())
        separator = Gtk.Separator()
        separator.add_css_class("system-sep")
        panel.append(separator)

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

        self.set_panel(panel)

    def settings_row(self):
        button = Gtk.Button()
        button.add_css_class("system-row")
        button.add_css_class("settings")
        row = Gtk.Box(spacing=12)
        row.append(Gtk.Image.new_from_icon_name("emblem-system-symbolic"))
        title = Gtk.Label(label="Nastavenia", xalign=0, hexpand=True)
        hint = Gtk.Label(label="systém a vzhľad", xalign=1)
        hint.add_css_class("system-hint")
        row.append(title)
        row.append(hint)
        button.set_child(row)
        button.connect("clicked", lambda _b: self.open_settings())
        return button

    def open_settings(self):
        self.close_menu()
        self.on_settings()

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
        button.connect("clicked", lambda _b, a=action, b=button: self.clicked(a, b))
        button.title_label = title
        button.hint_label = hint
        self.rows.append(button)
        return button

    # ---------- potvrdenie ----------
    def clicked(self, action, button):
        if not action.confirm or (self.confirming and self.confirming[0] is action):
            self.cancel_confirm()
            self.run(action)
            return
        self.cancel_confirm()
        button.add_css_class("confirm")
        button.title_label.set_text("Potvrdiť: " + action.label)
        button.hint_label.set_text("ešte raz")
        source = GLib.timeout_add(CONFIRM_MS, self.expire_confirm)
        self.confirming = (action, button, source)

    def cancel_confirm(self):
        """Vráti tlačidlo do pôvodného stavu a zruší časovač."""
        if self.confirming is None:
            return
        action, button, source = self.confirming
        self.confirming = None
        if source:
            GLib.source_remove(source)
        button.remove_css_class("confirm")
        button.title_label.set_text(action.label)
        button.hint_label.set_text(action.hint)

    def expire_confirm(self):
        if self.confirming is not None:
            self.confirming = self.confirming[:2] + (0,)      # zdroj sa po False odstráni sám
            self.cancel_confirm()
        return False

    def close_menu(self):
        self.cancel_confirm()
        super().close_menu()

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
