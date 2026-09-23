"""Portálový backend LatteOS: org.freedesktop.impl.portal.Settings.

xdg-desktop-portal (frontend) sa cez tento backend pýta na vzhľad; aplikácie (GTK4, libadwaita,
Flatpak, ...) ho čítajú od frontendu a dostávajú SettingChanged, keď sa hodnota zmení. Vďaka tomu sa
farebný režim, akcent a ďalšie prepnú za behu a bez súborov toolkitu. Hodnoty dodáva
appearance.portal_values (backend o motívoch nič nevie).
"""
import fnmatch
import sys
import warnings

from gi.repository import Gio, GLib

BUS_NAME = "org.freedesktop.impl.portal.desktop.latteos"
OBJECT_PATH = "/org/freedesktop/portal/desktop"
INTERFACE = "org.freedesktop.impl.portal.Settings"
VERSION = 2
NOT_FOUND = "org.freedesktop.portal.Error.NotFound"

XML = """<node><interface name="org.freedesktop.impl.portal.Settings">
 <method name="ReadAll"><arg type="as" name="namespaces" direction="in"/><arg type="a{sa{sv}}" name="value" direction="out"/></method>
 <method name="Read"><arg type="s" name="namespace" direction="in"/><arg type="s" name="key" direction="in"/><arg type="v" name="value" direction="out"/></method>
 <method name="ReadOne"><arg type="s" name="namespace" direction="in"/><arg type="s" name="key" direction="in"/><arg type="v" name="value" direction="out"/></method>
 <signal name="SettingChanged"><arg type="s" name="namespace"/><arg type="s" name="key"/><arg type="v" name="value"/></signal>
 <property name="version" type="u" access="read"/>
</interface></node>"""


def namespace_matches(namespace, patterns):
    """Prázdny zoznam = všetko; inak vzorky s hviezdičkou ("org.freedesktop.*")."""
    return not patterns or any(fnmatch.fnmatchcase(namespace, p) for p in patterns)


def to_variant(spec):
    signature, value = spec
    return GLib.Variant(signature, value)


class PortalBackend:
    """provider() vráti {menný priestor: {kľúč: (signatúra, hodnota)}}; refresh() pošle zmeny."""

    def __init__(self, provider):
        self.provider = provider
        self.values = provider()
        self.connection = None
        self.owner = 0

    # -------- D-Bus
    def start(self, on_lost=None):
        self.owner = Gio.bus_own_name(
            Gio.BusType.SESSION, BUS_NAME, Gio.BusNameOwnerFlags.NONE,
            self._acquired, None, on_lost or self._lost)

    def _lost(self, _conn, name):
        print("latte-appearance: meno %s sa nepodarilo získať (beží iný backend?)" % name, file=sys.stderr)
        sys.exit(1)

    def _acquired(self, connection, _name):
        self.connection = connection
        info = Gio.DBusNodeInfo.new_for_xml(XML).interfaces[0]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)      # register_object je v PyGObject označený ako zastaraný
            connection.register_object(OBJECT_PATH, info, self._method_call,
                                       lambda *_a: GLib.Variant("u", VERSION), None)

    def _method_call(self, _conn, _sender, _path, _iface, method, params, invocation):
        if method == "ReadAll":
            (patterns,) = params.unpack()
            result = {ns: {k: to_variant(spec) for k, spec in keys.items()}
                      for ns, keys in self.values.items() if namespace_matches(ns, patterns)}
            invocation.return_value(GLib.Variant("(a{sa{sv}})", (result,)))
        elif method in ("Read", "ReadOne"):
            namespace, key = params.unpack()
            spec = self.values.get(namespace, {}).get(key)
            if spec is None:
                invocation.return_dbus_error(NOT_FOUND, "Requested setting not found")
            else:
                invocation.return_value(GLib.Variant("(v)", (to_variant(spec),)))

    # -------- zmeny
    def refresh(self):
        """Prepočíta hodnoty a pošle SettingChanged pre všetko, čo sa zmenilo. Vráti počet zmien."""
        fresh = self.provider()
        changed = 0
        for namespace, keys in fresh.items():
            for key, spec in keys.items():
                if self.values.get(namespace, {}).get(key) != spec:
                    changed += 1
                    if self.connection is not None:
                        self.connection.emit_signal(
                            None, OBJECT_PATH, INTERFACE, "SettingChanged",
                            GLib.Variant("(ssv)", (namespace, key, to_variant(spec))))
        self.values = fresh
        return changed
