"""Úložiská cez udisks2 (bod 1.11, latte-storaged): sledovanie pripojenia diskov
a pripájanie či odpájanie zväzkov. Všetko cez systémovú zbernicu D-Bus.
"""
import os
import re
import sys

from gi.repository import Gio, GLib

UDISKS = "org.freedesktop.UDisks2"
ROOT_PATH = "/org/freedesktop/UDisks2"
FILESYSTEM = "org.freedesktop.UDisks2.Filesystem"
DEBOUNCE_MS = 400               # zlúčiť dávku udalostí z jedného pripojenia kľúča

_bus = None


def system_bus():
    global _bus
    if _bus is None:
        _bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    return _bus


class Watcher:
    """Volá on_changed() v hlavnom vlákne, keď sa objaví či zmizne disk alebo sa zmení
    jeho pripojenie. Rýchle po sebe idúce udalosti sa zlúčia do jedného volania."""

    def __init__(self, on_changed):
        self.on_changed = on_changed
        self.timer = 0
        self.subscriptions = []
        self.watch = 0
        self.bus = None

    def start(self):
        """Vráti None, alebo text, prečo sledovanie nefunguje (bez tichej degradácie)."""
        try:
            self.bus = system_bus()
        except GLib.Error as err:
            return "systémová zbernica nie je dostupná: " + err.message

        def subscribe(interface, member, path, arg0=None):
            self.subscriptions.append(self.bus.signal_subscribe(
                UDISKS, interface, member, path, arg0,
                Gio.DBusSignalFlags.NONE, self._signal, None))

        subscribe("org.freedesktop.DBus.ObjectManager", "InterfacesAdded", ROOT_PATH)
        subscribe("org.freedesktop.DBus.ObjectManager", "InterfacesRemoved", ROOT_PATH)
        # zmena MountPoints pri pripojení a odpojení
        subscribe("org.freedesktop.DBus.Properties", "PropertiesChanged", None, FILESYSTEM)

        # AUTO_START spustí udisksd, ak ešte nebeží; bez neho by signály neprišli
        self.watch = Gio.bus_watch_name_on_connection(
            self.bus, UDISKS, Gio.BusNameWatcherFlags.AUTO_START,
            lambda *_a: self._schedule(),
            lambda *_a: print("latte-storaged: udisks2 sa ukončil, sledovanie čaká", file=sys.stderr))
        return None

    def stop(self):
        for sub in self.subscriptions:
            self.bus.signal_unsubscribe(sub)
        self.subscriptions.clear()
        if self.watch:
            Gio.bus_unwatch_name(self.watch)
            self.watch = 0
        if self.timer:
            GLib.source_remove(self.timer)
            self.timer = 0

    def _signal(self, *_a):
        self._schedule()

    def _schedule(self):
        if self.timer:
            return
        self.timer = GLib.timeout_add(DEBOUNCE_MS, self._fire)

    def _fire(self):
        self.timer = 0
        self.on_changed()
        return False


# ---------------------------------------------------------------- pripojenie
def block_path(device):
    """/dev/sdb1 -> /org/freedesktop/UDisks2/block_devices/sdb1"""
    return ROOT_PATH + "/block_devices/" + os.path.basename(device)


def _filesystem_call(device, method, on_done):
    """on_done(výsledok: str | None, chyba: str | None) v hlavnom vlákne."""
    def finished(bus, task):
        try:
            reply = bus.call_finish(task)
        except GLib.Error as err:
            if Gio.DBusError.get_remote_error(err) == "org.freedesktop.UDisks2.Error.AlreadyMounted":
                on_done(None, None)
            else:
                # „GDBus.Error:org.freedesktop.…: text“ -> „text“
                on_done(None, re.sub(r"^GDBus\.Error:\S+?: ", "", err.message))
            return
        values = reply.unpack()
        on_done(values[0] if values else None, None)

    try:
        bus = system_bus()
    except GLib.Error as err:
        GLib.idle_add(lambda: (on_done(None, err.message), False)[1])
        return
    bus.call(
        UDISKS, block_path(device), FILESYSTEM, method,
        GLib.Variant("(a{sv})", ({},)), None,
        Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION, -1, None, finished)


def mount(device, on_done):
    """Pripojí zväzok (udisks ho pripojí pod /run/media/<používateľ>/...)."""
    _filesystem_call(device, "Mount", on_done)


def unmount(device, on_done):
    _filesystem_call(device, "Unmount", on_done)
