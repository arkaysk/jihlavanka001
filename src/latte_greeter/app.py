#!/usr/bin/env python3
"""latte-greeter: prihlasovacia obrazovka LatteOS (greetd).

Rozloženie: vľavo hore naposledy prihlásení používatelia, v strede prihlasovacia
karta, vľavo od nej napájacie menu, vpravo panel s oznamami (dnes karta o páde
poslednej relácie) a dole hodiny. Vzhľad berie z rovnakého latte.css ako lišta.

Greeter nikdy nespustí reláciu sám od seba: prihlásenie začne až kliknutím na
používateľa alebo Enterom. Inak by sa relácia, ktorá padá, spúšťala dokola.
"""
import os
import sys
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

from latte_common import build, lastexit, theme, wallpaper, widgets  # noqa: E402
from latte_greeter import greetd, power, sessions  # noqa: E402
from latte_greeter import state as state_mod  # noqa: E402
from latte_greeter import users as users_mod  # noqa: E402

CONFIRM_SECONDS = 6
BADGES = {"crash": "PÁD", "killed": "ZABITÁ", "error": "CHYBA", "missing": "CHYBA"}


def _label(text, css=None, xalign=0.0, wrap=False):
    label = Gtk.Label(label=text, xalign=xalign)
    if css:
        for name in css.split():
            label.add_css_class(name)
    if wrap:
        label.set_wrap(True)
        label.set_max_width_chars(34)
    return label


def crash_card(record):
    """Karta o páde poslednej relácie. Text skladá lastexit z overených polí."""
    title, detail = lastexit.describe(record)
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    card.add_css_class("card-item")
    head = Gtk.Box(spacing=8)
    badge = _label(BADGES.get(record.kind, "CHYBA"), "badge danger")
    head.append(badge)
    head.append(_label(record.when(), "dim"))
    card.append(head)
    card.append(_label(title, "info-title", wrap=True))
    card.append(_label(detail, wrap=True))
    card.append(_label("Diagnostika po prihlásení (aj v konzole):", "dim", wrap=True))
    command = _label(lastexit.DIAG_COMMAND, "mono")
    command.set_selectable(True)
    card.append(command)
    return card


class Greeter(Gtk.ApplicationWindow):
    def __init__(self, app, flow, user_list, session_list, state):
        super().__init__(application=app)
        self.add_css_class("latte-greeter")
        self.flow = flow
        self.users = user_list
        self.sessions = session_list
        self.state = state
        self.user = None            # vybraný používateľ (users.User)
        self.other_mode = False     # "Iný používateľ": meno sa píše ručne
        self.pending = None         # Outcome s výzvou, na ktorú čaká greetd
        self.pending_for = None     # pre ktoré meno je výzva
        self.busy = False
        self.confirming = None      # id akcie, ktorá čaká na potvrdenie
        self.chips = []

        overlay = Gtk.Overlay()
        overlay.set_child(self.build_backdrop())
        scrim = Gtk.Box()
        scrim.add_css_class("login-scrim")
        scrim.set_can_target(False)
        overlay.add_overlay(scrim)
        overlay.add_overlay(self.build_page())
        self.set_child(overlay)

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self.on_key)
        self.add_controller(keys)

        last = next((u for u in self.users if u.name == state.last_user), None)
        if last or self.users:
            self.select_user(last or self.users[0], begin=False)
        else:
            self.select_other(begin=False)

    # ---------- stavba ----------
    def build_backdrop(self):
        """Tapeta: ostrá; po začatí prihlasovania sa plynulo prelíše do rozmazanej."""
        path = wallpaper.system_path()
        self.backdrop = Gtk.Stack()
        self.backdrop.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.backdrop.set_transition_duration(350)
        self.backdrop.add_named(widgets.Wallpaper(path), "sharp")
        try:
            blurred = widgets.Wallpaper(path, blurred=True)
        except (GLib.Error, OSError):
            blurred = widgets.Wallpaper(path)
        self.backdrop.add_named(blurred, "blur")
        return self.backdrop

    def build_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        for side in ("start", "end", "top", "bottom"):
            getattr(page, "set_margin_" + side)(24)

        self.chip_row = Gtk.Box(spacing=8)
        self.chip_row.set_halign(Gtk.Align.START)
        for user in self.users:
            self.chip_row.append(self.build_chip(user))
        self.chip_row.append(self.build_chip(None))
        page.append(self.chip_row)

        middle = Gtk.CenterBox()
        middle.set_vexpand(True)
        middle.set_start_widget(self.build_power())
        middle.set_center_widget(self.build_card())
        self.info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.info.add_css_class("info-panel")
        self.info.set_size_request(300, -1)
        self.info.set_halign(Gtk.Align.END)
        self.info.set_valign(Gtk.Align.CENTER)
        middle.set_end_widget(self.info)
        page.append(middle)

        bottom = Gtk.Box()
        clock = widgets.ClockSegment()
        clock.set_can_focus(False)
        clock.set_focusable(False)
        clock.set_can_target(False)
        bottom.append(clock)
        note = _label("%s · %s" % (build.NAME, build.label().lower()), "build-note")
        note.set_hexpand(True)
        note.set_halign(Gtk.Align.END)
        note.set_valign(Gtk.Align.END)
        bottom.append(note)
        page.append(bottom)
        return page

    def build_chip(self, user):
        button = Gtk.Button()
        button.add_css_class("segment")
        button.add_css_class("user-chip")
        button.set_valign(Gtk.Align.CENTER)
        row = Gtk.Box(spacing=10)
        if user is None:
            row.append(widgets.Avatar("+", size=32))
            row.append(_label("Iný používateľ"))
            button.connect("clicked", lambda _b: self.select_other(begin=True))
        else:
            row.append(widgets.Avatar(user.title, user.avatar, size=32))
            row.append(_label(user.title))
            button.connect("clicked", lambda _b, u=user: self.on_chip(u))
        button.set_child(row)
        self.chips.append((user, button))
        return button

    def build_card(self):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.add_css_class("login-card")
        card.set_size_request(360, -1)
        card.set_halign(Gtk.Align.CENTER)
        card.set_valign(Gtk.Align.CENTER)

        self.avatar_slot = Gtk.Box()
        self.avatar_slot.set_halign(Gtk.Align.CENTER)
        card.append(self.avatar_slot)
        self.name_label = _label("", "login-name", xalign=0.5)
        card.append(self.name_label)
        self.sub_label = _label("", "dim", xalign=0.5)
        card.append(self.sub_label)

        self.name_entry = Gtk.Entry(placeholder_text="Meno používateľa")
        self.name_entry.connect("activate", lambda _e: self.submit())
        card.append(self.name_entry)

        row = Gtk.Box(spacing=8)
        self.pw_entry = Gtk.Entry(placeholder_text="Heslo", hexpand=True)
        self.pw_entry.set_visibility(False)
        self.pw_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.pw_entry.connect("activate", lambda _e: self.submit())
        self.go = Gtk.Button.new_from_icon_name("go-next-symbolic")
        self.go.add_css_class("go")
        self.go.connect("clicked", lambda _b: self.submit())
        row.append(self.pw_entry)
        row.append(self.go)
        card.append(row)

        self.message = _label("", "login-message", xalign=0.5, wrap=True)
        card.append(self.message)

        self.session_row = Gtk.Box(spacing=8)
        self.session_row.set_halign(Gtk.Align.CENTER)
        self.session_row.append(_label("Relácia", "dim"))
        self.dropdown = Gtk.DropDown.new_from_strings([s.name for s in self.sessions])
        self.session_row.append(self.dropdown)
        self.session_row.set_visible(len(self.sessions) > 1)
        card.append(self.session_row)
        return card

    def build_power(self):
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        panel.add_css_class("power-panel")
        panel.set_halign(Gtk.Align.START)
        panel.set_valign(Gtk.Align.CENTER)
        dev = sessions.is_dev()
        self.power_buttons = {}
        groups = [("pc", "POČÍTAČ")] + ([("latteos", "LATTEOS DEV")] if dev else [])
        for group, title in groups:
            panel.append(_label(title, "section-title"))
            for action in power.ACTIONS:
                if action.group == group:
                    panel.append(self.build_power_button(action, dev))
        return panel

    def build_power_button(self, action, dev):
        button = Gtk.Button()
        button.add_css_class("power-item")
        row = Gtk.Box(spacing=12)
        icon = Gtk.Image.new_from_icon_name(action.icon)
        icon.set_pixel_size(20)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title = _label(action.label)
        hint = _label(action.hint, "dim")
        text.append(title)
        text.append(hint)
        hint.set_visible(self.hint_shown(action, dev))
        row.append(icon)
        row.append(text)
        button.set_child(row)
        button.connect("clicked", lambda _b, a=action: self.on_power(a))
        self.power_buttons[action.id] = (button, title, hint)
        return button

    # ---------- výber používateľa ----------
    def on_chip(self, user):
        if self.busy:
            return
        if self.user is user and not self.other_mode and self.pending:
            self.pw_entry.grab_focus()
            return
        self.select_user(user, begin=True)

    def select_user(self, user, begin):
        self.user = user
        self.other_mode = False
        self.pending = None
        self.pending_for = None
        self.refresh_card()
        if begin:
            self.begin_auth(user.name)
        else:
            self.pw_entry.grab_focus()

    def select_other(self, begin):
        """Iný používateľ: meno sa píše ručne, prihlásenie začne Enterom."""
        if self.busy:
            return
        self.user = None
        self.other_mode = True
        self.pending = None
        self.pending_for = None
        self.refresh_card()
        if begin:
            self.run_async(self.flow.cancel, lambda _r: None)
            self.blur(False)
        self.name_entry.grab_focus()

    def refresh_card(self):
        child = self.avatar_slot.get_first_child()
        if child is not None:
            self.avatar_slot.remove(child)
        user = self.user
        if user is None:
            self.avatar_slot.append(widgets.Avatar("?", size=112))
            self.name_label.set_text("Iný používateľ")
            self.sub_label.set_visible(False)
        else:
            self.avatar_slot.append(widgets.Avatar(user.title, user.avatar, size=112))
            self.name_label.set_text(user.title)
            self.sub_label.set_text(user.name)
            self.sub_label.set_visible(bool(user.real_name) and user.real_name != user.name)
            remembered = self.state.sessions.get(user.name)
            for i, session in enumerate(self.sessions):
                if session.name == remembered:
                    self.dropdown.set_selected(i)
                    break
        self.name_entry.set_visible(self.other_mode)
        self.name_entry.set_text("")
        self.pw_entry.set_text("")
        self.pw_entry.set_visibility(False)
        self.pw_entry.set_placeholder_text("Heslo")
        self.set_message("")
        for chip_user, button in self.chips:
            selected = chip_user is None if self.other_mode else chip_user is user
            (button.add_css_class if selected else button.remove_css_class)("selected")
        self.refresh_info()

    def refresh_info(self):
        while (child := self.info.get_first_child()) is not None:
            self.info.remove(child)
        # Sem pribudnú ďalšie karty (počasie, RSS), ak si ich používateľ povolí;
        # kartu o páde skladá lastexit, ostatné zdroje nemá greeter sťahovať sám.
        record = lastexit.read(self.user.name) if self.user else None
        if record:
            self.info.append(crash_card(record))
        self.info.set_visible(record is not None)

    # ---------- prihlasovanie ----------
    def submit(self):
        if self.busy:
            return
        if self.other_mode:
            name = self.name_entry.get_text().strip()
            if not name:
                self.name_entry.grab_focus()
                return
            self.user = users_mod.User(name, "", -1)
        name = self.user.name
        text = self.pw_entry.get_text()
        if self.pending and self.pending_for == name:
            self.send_answer(text)
        else:
            self.begin_auth(name, carry=text)

    def begin_auth(self, name, carry=""):
        self.set_message("")
        self.blur(True)
        self.run_async(
            lambda: self.flow.begin(name),
            lambda outcome: self.on_outcome(outcome, name, carry, first=True),
        )

    def send_answer(self, text):
        name = self.pending_for
        self.pw_entry.set_text("")
        self.run_async(
            lambda: self.flow.answer(text),
            lambda outcome: self.on_outcome(outcome, name),
        )

    def on_outcome(self, outcome, name, carry="", first=False):
        if isinstance(outcome, Exception):
            self.pending = None
            self.blur(False)
            self.set_message(str(outcome), error=True)
            return
        for note in outcome.notes:
            self.set_message(note)
        if outcome.kind == "success":
            self.pending = None
            if first and not carry:
                self.set_message("Účet nemá heslo, prihlasujem…")
            else:
                self.set_message("Prihlasujem…")
            self.finish_login(name)
        elif outcome.kind == "prompt":
            self.pending = outcome
            self.pending_for = name
            self.pw_entry.set_visibility(not outcome.secret)
            self.pw_entry.set_placeholder_text(self.prompt_text(outcome))
            if carry:
                self.send_answer(carry)
            else:
                self.pw_entry.grab_focus()
        else:
            self.pending = None
            self.blur(False)
            if outcome.auth_error:
                self.set_message("Nesprávne heslo alebo meno.", error=True)
                self.pw_entry.select_region(0, -1)
            else:
                self.set_message(outcome.text, error=True)
            self.pw_entry.grab_focus()

    @staticmethod
    def prompt_text(outcome):
        text = outcome.text.strip().rstrip(":").strip()
        if outcome.secret and text.lower() in ("password", "heslo", ""):
            return "Heslo"
        return text or "Heslo"

    def finish_login(self, name):
        session = self.sessions[self.dropdown.get_selected()]

        def start():
            # Stav sa uloží pred odovzdaním relácie: po nej greetd greeter ukončí.
            self.state.record_login(name, session.name)
            return self.flow.start(session.cmd)

        self.run_async(start, self.on_started)

    def on_started(self, outcome):
        if isinstance(outcome, Exception) or outcome.kind != "success":
            text = str(outcome) if isinstance(outcome, Exception) else outcome.text
            self.blur(False)
            self.set_message("Reláciu sa nepodarilo spustiť: " + text, error=True)
            return
        self.get_application().quit()

    def cancel(self):
        """Esc: zruší rozbehnuté prihlásenie a vráti kartu do východiskového stavu."""
        if self.busy:
            return
        self.pending = None
        self.pending_for = None
        self.pw_entry.set_text("")
        self.pw_entry.set_visibility(False)
        self.pw_entry.set_placeholder_text("Heslo")
        self.set_message("")
        self.run_async(self.flow.cancel, lambda _r: None)
        self.blur(False)

    def on_key(self, _ctrl, keyval, _code, _state):
        if keyval == Gdk.KEY_Escape:
            self.cancel()
            return True
        return False

    # ---------- napájanie ----------
    def on_power(self, action):
        if self.busy:
            return
        if action.group != "pc" or self.confirming == action.id:
            self.confirming = None
            self.reset_power_labels()
            self.run_async(lambda: power.run(action), self.on_power_done)
            return
        self.run_async(power.other_users, lambda names: self.after_check(action, names))

    def after_check(self, action, names):
        if isinstance(names, Exception) or not names:
            self.run_async(lambda: power.run(action), self.on_power_done)
            return
        self.reset_power_labels()
        button, title, hint = self.power_buttons[action.id]
        self.confirming = action.id
        button.add_css_class("confirm")
        title.set_text("Potvrdiť: " + action.label)
        hint.set_text("Prihlásený je aj: " + ", ".join(names))
        hint.set_visible(True)
        GLib.timeout_add_seconds(CONFIRM_SECONDS, self.reset_power_labels)

    def reset_power_labels(self):
        self.confirming = None
        dev = sessions.is_dev()
        for action in power.ACTIONS:
            button, title, hint = self.power_buttons.get(action.id, (None, None, None))
            if button is not None:
                button.remove_css_class("confirm")
                title.set_text(action.label)
                hint.set_text(action.hint)
                hint.set_visible(self.hint_shown(action, dev))
        return False

    @staticmethod
    def hint_shown(action, dev):
        # "virtuálny stroj" má zmysel len vo vývoji
        return dev or action.group != "pc"

    def on_power_done(self, error):
        if isinstance(error, Exception):
            error = str(error)
        if error:
            self.set_message("Akciu odmietol systém: " + error, error=True)

    # ---------- pomocné ----------
    def blur(self, on):
        self.backdrop.set_visible_child_name("blur" if on else "sharp")

    def set_message(self, text, error=False):
        self.message.set_text(text)
        self.message.set_visible(bool(text))
        (self.message.add_css_class if error else self.message.remove_css_class)("error")

    def focus_input(self):
        if self.other_mode and not self.name_entry.get_text():
            self.name_entry.grab_focus()
        else:
            self.pw_entry.grab_focus()

    def set_busy(self, busy):
        self.busy = busy
        for widget in (self.pw_entry, self.name_entry, self.go):
            widget.set_sensitive(not busy)

    def run_async(self, func, done):
        """Spustí blokujúce volanie vo vlákne, výsledok (alebo výnimku) odovzdá rozhraniu."""
        self.set_busy(True)

        def worker():
            try:
                result = func()
            except Exception as err:      # noqa: BLE001 - chyba sa ukáže používateľovi
                result = err
            GLib.idle_add(finish, result)

        def finish(result):
            self.set_busy(False)
            done(result)
            if not self.busy:               # done() mohlo začať ďalší krok
                self.focus_input()
            return False

        threading.Thread(target=worker, daemon=True).start()


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.latteos.Greeter")

    def do_activate(self):
        theme.load(Gdk.Display.get_default())
        state = state_mod.State.load()
        win = Greeter(
            self,
            greetd.LoginFlow(),
            users_mod.list_users(state.recent),
            sessions.load(),
            state,
        )
        win.present()
        if os.environ.get("LATTE_GREETER_WINDOWED"):
            win.set_default_size(1280, 720)     # vývoj: v okne, nie na celú obrazovku
        else:
            win.fullscreen()


if __name__ == "__main__":
    sys.exit(App().run(sys.argv))
