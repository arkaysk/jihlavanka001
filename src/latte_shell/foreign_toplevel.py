"""Zoznam okien cez protokol wlr-foreign-toplevel-management-v1.

Minimálny klient Wayland protokolu bez závislostí: hovorí priamo cez soket
a číta ho v slučke GLib. Vie len to, čo lišta potrebuje: zoznam okien, ich
názov, aplikáciu a stav, a povely aktivovať, minimalizovať a zavrieť.
"""
import os
import socket
import struct
import sys
import traceback

from gi.repository import GLib

MANAGER_IFACE = "zwlr_foreign_toplevel_manager_v1"
MANAGER_VERSION = 3

# wl_display (objekt 1)
DISPLAY = 1
DISPLAY_SYNC, DISPLAY_GET_REGISTRY = 0, 1
DISPLAY_ERROR = 0
# wl_registry
REGISTRY_BIND = 0
REGISTRY_GLOBAL = 0
# zwlr_foreign_toplevel_manager_v1
MANAGER_TOPLEVEL, MANAGER_FINISHED = 0, 1
# zwlr_foreign_toplevel_handle_v1: udalosti
EV_TITLE, EV_APP_ID, EV_STATE, EV_DONE, EV_CLOSED = 0, 1, 4, 5, 6
# zwlr_foreign_toplevel_handle_v1: povely
REQ_SET_MINIMIZED, REQ_UNSET_MINIMIZED, REQ_ACTIVATE, REQ_CLOSE, REQ_DESTROY = 2, 3, 4, 5, 7
STATE_MINIMIZED, STATE_ACTIVATED = 1, 2


def _string(text):
    raw = text.encode() + b"\0"
    return struct.pack("=I", len(raw)) + raw + b"\0" * (-len(raw) % 4)


def _read_string(data, offset):
    (size,) = struct.unpack_from("=I", data, offset)
    text = data[offset + 4:offset + 4 + size - 1].decode(errors="replace")
    return text, offset + 4 + ((size + 3) & ~3)


class Toplevel:
    def __init__(self, obj_id):
        self.id = obj_id
        self.title = ""
        self.app_id = ""
        self.minimized = False
        self.activated = False


class ForeignToplevels:
    """on_changed(top) po každom `done`, on_closed(top), on_unavailable(dôvod)."""

    def __init__(self, on_changed, on_closed, on_unavailable):
        self.on_changed = on_changed
        self.on_closed = on_closed
        self.on_unavailable = on_unavailable
        self.toplevels = {}
        self.sock = None
        self.buf = bytearray()
        self.last_id = DISPLAY
        self.registry = None
        self.sync = None
        self.manager = None
        self.seat = None

    # -------- spojenie --------
    def start(self):
        try:
            name = os.environ["WAYLAND_DISPLAY"]
            if not os.path.isabs(name):
                name = os.path.join(os.environ["XDG_RUNTIME_DIR"], name)
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(name)
        except KeyError as err:
            self.on_unavailable("chýba premenná " + err.args[0])
            return
        except OSError as err:
            self.on_unavailable("nepodarilo sa pripojiť ku kompozitoru (" + str(err) + ")")
            return

        self.registry = self._new_id()
        self._send(DISPLAY, DISPLAY_GET_REGISTRY, struct.pack("=I", self.registry))
        self.sync = self._new_id()
        self._send(DISPLAY, DISPLAY_SYNC, struct.pack("=I", self.sync))
        GLib.io_add_watch(
            self.sock.fileno(),
            GLib.PRIORITY_DEFAULT,
            GLib.IOCondition.IN | GLib.IOCondition.HUP | GLib.IOCondition.ERR,
            self._readable,
        )

    def _new_id(self):
        self.last_id += 1
        return self.last_id

    def _send(self, obj, opcode, payload=b""):
        header = struct.pack("=II", obj, ((8 + len(payload)) << 16) | opcode)
        self.sock.sendall(header + payload)

    def _lost(self, reason):
        self.toplevels.clear()
        self.on_unavailable(reason)
        return False

    def _readable(self, _fd, _condition):
        try:
            data = self.sock.recv(65536)
        except OSError as err:
            return self._lost("spojenie s kompozitorom zlyhalo (" + str(err) + ")")
        if not data:
            return self._lost("spojenie s kompozitorom sa prerušilo")
        self.buf += data
        while len(self.buf) >= 8:
            obj, word = struct.unpack_from("=II", self.buf)
            size, opcode = word >> 16, word & 0xFFFF
            if len(self.buf) < size:
                break
            payload = bytes(self.buf[8:size])
            del self.buf[:size]
            try:
                self._dispatch(obj, opcode, payload)
            except Exception:           # jedna zlá udalosť nesmie zrušiť sledovanie okien
                traceback.print_exc()
        return True

    # -------- udalosti --------
    def _dispatch(self, obj, opcode, payload):
        if obj == DISPLAY:
            if opcode == DISPLAY_ERROR:
                _obj, code = struct.unpack_from("=II", payload)
                message, _ = _read_string(payload, 8)
                print("latte-shell: chyba protokolu %d: %s" % (code, message), file=sys.stderr)
        elif obj == self.registry:
            if opcode == REGISTRY_GLOBAL:
                (name,) = struct.unpack_from("=I", payload)
                iface, offset = _read_string(payload, 4)
                (version,) = struct.unpack_from("=I", payload, offset)
                self._on_global(name, iface, version)
        elif obj == self.sync:
            if self.manager is None:
                self._lost("kompozitor nepodporuje wlr-foreign-toplevel-management")
        elif obj == self.manager:
            if opcode == MANAGER_TOPLEVEL:
                (new_id,) = struct.unpack_from("=I", payload)
                self.toplevels[new_id] = Toplevel(new_id)
            elif opcode == MANAGER_FINISHED:
                self._lost("kompozitor ukončil zoznam okien")
        elif obj in self.toplevels:
            self._on_toplevel(self.toplevels[obj], opcode, payload)

    def _bind(self, name, iface, version):
        new_id = self._new_id()
        payload = struct.pack("=I", name) + _string(iface) + struct.pack("=II", version, new_id)
        self._send(self.registry, REGISTRY_BIND, payload)
        return new_id

    def _on_global(self, name, iface, version):
        if iface == MANAGER_IFACE:
            self.manager = self._bind(name, iface, min(version, MANAGER_VERSION))
        elif iface == "wl_seat" and self.seat is None:
            self.seat = self._bind(name, iface, 1)

    def _on_toplevel(self, top, opcode, payload):
        if opcode == EV_TITLE:
            top.title, _ = _read_string(payload, 0)
        elif opcode == EV_APP_ID:
            top.app_id, _ = _read_string(payload, 0)
        elif opcode == EV_STATE:
            (size,) = struct.unpack_from("=I", payload)
            states = struct.unpack_from("=%dI" % (size // 4), payload, 4)
            top.minimized = STATE_MINIMIZED in states
            top.activated = STATE_ACTIVATED in states
        elif opcode == EV_DONE:
            self.on_changed(top)
        elif opcode == EV_CLOSED:
            del self.toplevels[top.id]
            self._send(top.id, REQ_DESTROY)
            self.on_closed(top)

    # -------- povely --------
    def activate(self, top):
        if self.seat is not None:
            self._send(top.id, REQ_ACTIVATE, struct.pack("=I", self.seat))

    def minimize(self, top):
        self._send(top.id, REQ_SET_MINIMIZED)

    def unminimize(self, top):
        self._send(top.id, REQ_UNSET_MINIMIZED)

    def close(self, top):
        self._send(top.id, REQ_CLOSE)
