"""D-Bus služba org.freedesktop.Notifications nad modelom oznámení (bod 2.7).

Bez GTK. Objekt sa dá zaregistrovať na akékoľvek spojenie (aj priame spojenie v testoch),
meno na zbernici získa own_name().
"""
import sys

from gi.repository import Gio, GLib  # noqa: E402

NAME = "org.freedesktop.Notifications"
PATH = "/org/freedesktop/Notifications"
VERSION = "0.1"

INTROSPECTION = """
<node>
  <interface name="org.freedesktop.Notifications">
    <method name="GetCapabilities">
      <arg direction="out" type="as" name="capabilities"/>
    </method>
    <method name="Notify">
      <arg direction="in" type="s" name="app_name"/>
      <arg direction="in" type="u" name="replaces_id"/>
      <arg direction="in" type="s" name="app_icon"/>
      <arg direction="in" type="s" name="summary"/>
      <arg direction="in" type="s" name="body"/>
      <arg direction="in" type="as" name="actions"/>
      <arg direction="in" type="a{sv}" name="hints"/>
      <arg direction="in" type="i" name="expire_timeout"/>
      <arg direction="out" type="u" name="id"/>
    </method>
    <method name="CloseNotification">
      <arg direction="in" type="u" name="id"/>
    </method>
    <method name="GetServerInformation">
      <arg direction="out" type="s" name="name"/>
      <arg direction="out" type="s" name="vendor"/>
      <arg direction="out" type="s" name="version"/>
      <arg direction="out" type="s" name="spec_version"/>
    </method>
    <signal name="NotificationClosed">
      <arg type="u" name="id"/>
      <arg type="u" name="reason"/>
    </signal>
    <signal name="ActionInvoked">
      <arg type="u" name="id"/>
      <arg type="s" name="action_key"/>
    </signal>
  </interface>
</node>
"""

# body-markup nie je: telo sa ukazuje ako obyčajný text
CAPABILITIES = ["body", "actions"]


class Service:
    def __init__(self, center):
        self.center = center
        self.connection = None
        self.owner_id = 0
        self.problem = ""               # prečo služba nebeží ("" = beží alebo sa ešte štartuje)
        center.on_closed = self.closed
        center.on_action = self.action
        self.info = Gio.DBusNodeInfo.new_for_xml(INTROSPECTION).interfaces[0]

    # ---------- pripojenie ----------
    def export(self, connection):
        self.connection = connection
        connection.register_object(PATH, self.info, self.method_call, None, None)

    def own_name(self):
        self.owner_id = Gio.bus_own_name(
            Gio.BusType.SESSION, NAME, Gio.BusNameOwnerFlags.NONE,
            lambda conn, _name: self.export(conn),
            lambda _conn, _name: None,
            self.name_lost,
        )

    def name_lost(self, _connection, _name):
        self.problem = ("meno %s drží iný démon oznámení alebo zbernica nie je dostupná, "
                        "oznámenia nebudú fungovať" % NAME)
        print("latte-shell:", self.problem, file=sys.stderr)

    # ---------- volania ----------
    def method_call(self, _connection, _sender, _path, _iface, method, params, invocation):
        try:
            if method == "GetCapabilities":
                invocation.return_value(GLib.Variant("(as)", (CAPABILITIES,)))
            elif method == "Notify":
                app, replaces, icon, summary, body, actions, hints, timeout = params.unpack()
                nid = self.center.notify(app, replaces, icon, summary, body, actions, hints, timeout)
                invocation.return_value(GLib.Variant("(u)", (nid,)))
            elif method == "CloseNotification":
                self.center.close(params.unpack()[0], 3)
                invocation.return_value(None)
            elif method == "GetServerInformation":
                invocation.return_value(GLib.Variant("(ssss)", ("latte-shell", "LatteOS", VERSION, "1.2")))
            else:
                invocation.return_dbus_error("org.freedesktop.DBus.Error.UnknownMethod", method)
        except Exception as err:            # chyba v jednom volaní nesmie zhodiť lištu
            print("latte-shell: oznámenie zlyhalo:", err, file=sys.stderr)
            invocation.return_dbus_error("org.freedesktop.DBus.Error.Failed", str(err))

    # ---------- signály ----------
    def emit(self, name, params):
        if self.connection is not None:
            self.connection.emit_signal(None, PATH, NAME, name, params)

    def closed(self, nid, reason):
        self.emit("NotificationClosed", GLib.Variant("(uu)", (nid, reason)))

    def action(self, nid, key):
        self.emit("ActionInvoked", GLib.Variant("(us)", (nid, key)))
