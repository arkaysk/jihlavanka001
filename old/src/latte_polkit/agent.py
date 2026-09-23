#!/usr/bin/env python3
"""latte-polkit: polkit agent relácie LatteOS.

Bez agenta by pkexec (a teda „vykonať ako správca“ v správcovi súborov) nemal kde
vypýtať heslo. Beží ako user služba pod latte-session.target.
"""
import grp
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Polkit", "1.0")
gi.require_version("PolkitAgent", "1.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Polkit, PolkitAgent  # noqa: E402

from latte_common import theme  # noqa: E402

OBJECT_PATH = "/org/latteos/PolicyKit1/AuthenticationAgent"


def user_name(identity):
    if isinstance(identity, Polkit.UnixUser):
        return identity.get_name() if hasattr(identity, "get_name") else str(identity.get_uid())
    return identity.to_string()


def expand(identities):
    """Skupiny (napr. wheel) rozvinie na používateľov; poradie a duplicity ošetrí."""
    users = []
    seen = set()

    def add(ident):
        key = ident.to_string()
        if key not in seen:
            seen.add(key)
            users.append(ident)

    for ident in identities:
        if isinstance(ident, Polkit.UnixGroup):
            try:
                for name in grp.getgrgid(ident.get_gid()).gr_mem:
                    add(Polkit.UnixUser.new_for_name(name))
            except (KeyError, GLib.Error):
                continue
        elif isinstance(ident, Polkit.UnixUser):
            add(ident)
    return users


def choose(identities):
    """Najprv sám používateľ (je v skupine správcov), inak prvý z ponúknutých (root)."""
    users = expand(identities)
    me = os.getuid()
    for ident in users:
        if ident.get_uid() == me:
            return ident
    return users[0] if users else None


class AuthDialog(Gtk.Window):
    def __init__(self, message, identity, on_response, on_cancel):
        super().__init__(title="Overenie totožnosti")
        self.set_default_size(420, -1)
        self.set_resizable(False)
        self.identity = identity
        self.on_response = on_response
        self.on_cancel = on_cancel
        self.add_css_class("auth-dialog")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        for f in (box.set_margin_top, box.set_margin_bottom, box.set_margin_start, box.set_margin_end):
            f(20)
        head = Gtk.Label(label="Overenie totožnosti", xalign=0)
        head.add_css_class("title-3")
        self.message = Gtk.Label(label=message, wrap=True, xalign=0)
        self.prompt = Gtk.Label(label="", xalign=0)
        self.prompt.add_css_class("dim-label")
        self.entry = Gtk.PasswordEntry(show_peek_icon=True)
        self.entry.set_sensitive(False)
        self.status = Gtk.Label(label="", wrap=True, xalign=0)
        self.status.add_css_class("error")
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, halign=Gtk.Align.END)
        self.cancel_btn = Gtk.Button(label="Zrušiť")
        self.ok_btn = Gtk.Button(label="Overiť")
        self.ok_btn.add_css_class("suggested-action")
        self.ok_btn.set_sensitive(False)
        row.append(self.cancel_btn)
        row.append(self.ok_btn)
        for w in (head, self.message, self.prompt, self.entry, self.status, row):
            box.append(w)
        self.set_child(box)

        self.cancel_btn.connect("clicked", lambda _b: self.on_cancel())
        self.ok_btn.connect("clicked", self.submit)
        self.entry.connect("activate", self.submit)
        self.connect("close-request", lambda _w: (self.on_cancel(), True)[1])

    def ask(self, prompt, echo_on):
        """PAM žiada odpoveď (zvyčajne heslo)."""
        name = user_name(self.identity)
        if prompt.strip().lower().startswith("password"):
            prompt = "Heslo používateľa %s:" % name
        self.prompt.set_text(prompt)
        self.entry.set_text("")
        self.entry.set_sensitive(True)
        self.ok_btn.set_sensitive(True)
        self.entry.grab_focus()

    def submit(self, *_a):
        text = self.entry.get_text()
        self.entry.set_sensitive(False)
        self.ok_btn.set_sensitive(False)
        self.on_response(text)

    def show_status(self, text):
        self.status.set_text(text)


class Attempt:
    """Jedno overenie: PolkitAgent.Session drží rozhovor s PAM, dialóg ho zobrazuje."""

    def __init__(self, agent, invocation, message, cookie, identity):
        self.agent = agent
        self.invocation = invocation
        self.cookie = cookie
        self.identity = identity
        self.finished = False
        self.session = None
        self.retired = []           # staré Session sa neuvoľňujú vo vlastnom signáli (pád)
        self.dialog = AuthDialog(message, identity, self.respond, self.cancel)
        self.dialog.present()
        self.begin()

    def begin(self):
        self.session = PolkitAgent.Session.new(self.identity, self.cookie)
        self.session.connect("request", lambda _s, prompt, echo: self.dialog.ask(prompt, echo))
        self.session.connect("show-error", lambda _s, text: self.dialog.show_status(text))
        self.session.connect("show-info", lambda _s, text: self.dialog.show_status(text))
        self.session.connect("completed", self.completed)
        self.session.initiate()

    def respond(self, text):
        self.session.response(text)

    def completed(self, _session, gained):
        if self.finished:
            return
        if gained:
            GLib.idle_add(self.finish, True)
        else:
            # zlé heslo: nový pokus v tom istom dialógu, kým používateľ nezruší
            self.dialog.show_status("Overenie zlyhalo. Skúste to znova.")
            self.retired.append(self.session)
            GLib.idle_add(self.retry)

    def retry(self):
        if not self.finished:
            self.begin()
        return False

    def cancel(self):
        if self.finished:
            return False
        if self.session is not None:
            self.session.cancel()
        self.finish(False)
        return False

    def finish(self, ok):
        if self.finished:
            return False
        self.finished = True
        self.dialog.destroy()
        if ok:
            self.invocation.return_value(None)
        else:
            self.invocation.return_dbus_error("org.freedesktop.PolicyKit1.Error.Cancelled", "Overenie zrušené")
        self.agent.attempts.pop(self.cookie, None)
        return False


AGENT_XML = """
<node>
  <interface name="org.freedesktop.PolicyKit1.AuthenticationAgent">
    <method name="BeginAuthentication">
      <arg type="s" name="action_id" direction="in"/>
      <arg type="s" name="message" direction="in"/>
      <arg type="s" name="icon_name" direction="in"/>
      <arg type="a{ss}" name="details" direction="in"/>
      <arg type="s" name="cookie" direction="in"/>
      <arg type="a(sa{sv})" name="identities" direction="in"/>
    </method>
    <method name="CancelAuthentication">
      <arg type="s" name="cookie" direction="in"/>
    </method>
  </interface>
</node>
"""


def identity_from_variant(kind, props):
    if kind == "unix-user":
        return Polkit.UnixUser.new(props["uid"])
    if kind == "unix-group":
        return Polkit.UnixGroup.new(props["gid"])
    return None


class Agent:
    """Agent polkitu cez D-Bus. PolkitAgent.Listener sa nedá použiť z Pythonu: PyGObject
    zahodí user_data asynchrónneho vfuncu a pád nastane až pri dokončení overenia."""

    def __init__(self):
        self.attempts = {}          # cookie -> Attempt
        self.bus = None

    def register(self):
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        info = Gio.DBusNodeInfo.new_for_xml(AGENT_XML).interfaces[0]
        self.bus.register_object(OBJECT_PATH, info, self.on_call, None, None)
        locale = os.environ.get("LC_ALL") or os.environ.get("LANG") or "sk_SK.UTF-8"
        session = ("unix-session", {"session-id": GLib.Variant("s", session_id())})
        self.bus.call_sync(
            "org.freedesktop.PolicyKit1", "/org/freedesktop/PolicyKit1/Authority",
            "org.freedesktop.PolicyKit1.Authority", "RegisterAuthenticationAgent",
            GLib.Variant("((sa{sv})ss)", (session, locale, OBJECT_PATH)),
            None, Gio.DBusCallFlags.NONE, -1, None)

    def on_call(self, _conn, _sender, _path, _iface, method, params, invocation):
        if method == "CancelAuthentication":
            attempt = self.attempts.get(params.unpack()[0])
            if attempt is not None:
                attempt.cancel()
            invocation.return_value(None)
            return
        _action, message, _icon, _details, cookie, raw = params.unpack()
        identity = choose([i for i in (identity_from_variant(k, p) for k, p in raw) if i is not None])
        if identity is None:
            invocation.return_dbus_error("org.freedesktop.PolicyKit1.Error.Failed", "Žiadny správca nie je k dispozícii")
            return
        self.attempts[cookie] = Attempt(self, invocation, message, cookie, identity)


def session_id():
    """Relácia, pre ktorú agent žiada o overenia. Služba pod systemd nie je v scope relácie,
    preto sa berie XDG_SESSION_ID z prostredia odovzdaného autostartom."""
    value = os.environ.get("XDG_SESSION_ID")
    if value:
        return value
    return Polkit.UnixSession.new_for_process_sync(os.getpid(), None).get_session_id()


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.latteos.Polkit")
        self.agent = None

    def do_activate(self):
        if self.agent is not None:
            return
        theme.load(Gdk.Display.get_default())
        try:
            self.agent = Agent()
            self.agent.register()
        except GLib.Error as err:
            print("latte-polkit: agent sa nepodarilo zaregistrovať:", err.message, file=sys.stderr)
            sys.exit(1)
        self.hold()


if __name__ == "__main__":
    App().run(sys.argv)
