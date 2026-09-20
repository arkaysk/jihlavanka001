"""Výstupy (monitory) cez protokol wlr-output-management-unstable-v1.

Minimálny synchrónny klient bez závislostí (rovnaký prístup ako latte_shell/foreign_toplevel.py):
pripojí sa ku kompozitoru, prečíta zoznam monitorov s režimami a vie použiť novú konfiguráciu.
Spojenie je krátke: načítať, prípadne zmeniť, zavrieť. Nič sa tu neukladá; trvalosť rieši displays.py.

Zdroj pravdy o tom, čo monitor vie a čo má práve nastavené, je kompozitor (EDID číta on),
preto ho tu nič nehádame zo sysfs.
"""
import os
import select
import socket
import struct
import time
from dataclasses import dataclass, field

MANAGER_IFACE = "zwlr_output_manager_v1"
MANAGER_VERSION = 4
TIMEOUT = 3.0

# wl_display (objekt 1)
DISPLAY = 1
DISPLAY_SYNC, DISPLAY_GET_REGISTRY = 0, 1
DISPLAY_ERROR = 0
REGISTRY_BIND = 0
REGISTRY_GLOBAL = 0
CALLBACK_DONE = 0
# zwlr_output_manager_v1
MGR_HEAD, MGR_DONE, MGR_FINISHED = 0, 1, 2
MGR_CREATE_CONFIGURATION, MGR_STOP = 0, 1
# zwlr_output_head_v1: udalosti
(H_NAME, H_DESCRIPTION, H_PHYSICAL_SIZE, H_MODE, H_ENABLED, H_CURRENT_MODE, H_POSITION,
 H_TRANSFORM, H_SCALE, H_FINISHED, H_MAKE, H_MODEL, H_SERIAL) = range(13)
# zwlr_output_mode_v1: udalosti
M_SIZE, M_REFRESH, M_PREFERRED, M_FINISHED = range(4)
# zwlr_output_configuration_v1
CFG_ENABLE_HEAD, CFG_DISABLE_HEAD, CFG_APPLY, CFG_TEST, CFG_DESTROY = range(5)
CFG_SUCCEEDED, CFG_FAILED, CFG_CANCELLED = range(3)
# zwlr_output_configuration_head_v1
(CH_SET_MODE, CH_SET_CUSTOM_MODE, CH_SET_POSITION, CH_SET_TRANSFORM, CH_SET_SCALE, CH_DESTROY) = range(6)

# wl_output.transform
TRANSFORMS = {0: "normal", 1: "90", 2: "180", 3: "270",
              4: "flipped", 5: "flipped-90", 6: "flipped-180", 7: "flipped-270"}
TRANSFORM_IDS = {name: number for number, name in TRANSFORMS.items()}


class OutputsError(RuntimeError):
    """Kompozitor nie je dostupný, nepodporuje správu výstupov alebo zmenu odmietol."""


@dataclass
class Mode:
    id: int
    width: int = 0
    height: int = 0
    refresh: int = 0            # mHz (60000 = 60 Hz); 0 = neznáme
    preferred: bool = False

    @property
    def hz(self):
        return self.refresh / 1000.0


@dataclass
class Head:
    id: int
    name: str = ""              # konektor: eDP-1, HDMI-A-1, ...
    description: str = ""
    make: str = ""
    model: str = ""
    serial: str = ""
    width_mm: int = 0
    height_mm: int = 0
    enabled: bool = True
    modes: dict = field(default_factory=dict)       # id objektu -> Mode
    current_mode: int = 0       # id objektu Mode, 0 = žiadny
    x: int = 0
    y: int = 0
    transform: int = 0
    scale: float = 1.0
    finished: bool = False

    @property
    def current(self):
        return self.modes.get(self.current_mode)


def _string(text):
    raw = text.encode() + b"\0"
    return struct.pack("=I", len(raw)) + raw + b"\0" * (-len(raw) % 4)


def _read_string(data, offset):
    (size,) = struct.unpack_from("=I", data, offset)
    text = data[offset + 4:offset + 4 + max(size - 1, 0)].decode(errors="replace") if size else ""
    return text, offset + 4 + ((size + 3) & ~3)


def _fixed(value):
    return int(round(value * 256))


class Client:
    """Spojenie s kompozitorom. Po connect() sú v .heads aktuálne monitory."""

    def __init__(self, timeout=TIMEOUT):
        self.timeout = timeout
        self.sock = None
        self.buf = bytearray()
        self.last_id = DISPLAY
        self.registry = None
        self.manager = None
        self.serial = None
        self.heads = {}         # id objektu -> Head
        self.mode_owner = {}    # id objektu Mode -> Head
        self.result = {}        # id konfigurácie -> None (čaká) | succeeded | failed | cancelled
        self.callbacks = set()

    # ---------- spojenie ----------
    def connect(self):
        try:
            name = os.environ["WAYLAND_DISPLAY"]
            if not os.path.isabs(name):
                name = os.path.join(os.environ["XDG_RUNTIME_DIR"], name)
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(name)
        except KeyError as err:
            raise OutputsError("chýba premenná %s (nebeží grafická relácia?)" % err.args[0]) from None
        except OSError as err:
            raise OutputsError("nepodarilo sa pripojiť ku kompozitoru: %s" % err) from None
        try:
            self.registry = self._new_id()
            self._send(DISPLAY, DISPLAY_GET_REGISTRY, struct.pack("=I", self.registry))
            self.roundtrip()
            if self.manager is None:
                raise OutputsError("kompozitor nepodporuje správu výstupov (wlr-output-management)")
            self.roundtrip()
        except OutputsError:
            self.close()                # `with` sa pri zlyhaní connect() nevolá, socket by unikol
            raise
        return self

    def close(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, *_exc):
        self.close()

    def _new_id(self):
        self.last_id += 1
        return self.last_id

    def _send(self, obj, opcode, payload=b""):
        header = struct.pack("=II", obj, ((8 + len(payload)) << 16) | opcode)
        try:
            self.sock.sendall(header + payload)
        except OSError as err:
            raise OutputsError("spojenie s kompozitorom zlyhalo: %s" % err) from None

    def _pump(self, deadline):
        """Prečíta a spracuje, čo je k dispozícii (najviac do deadline)."""
        left = deadline - time.monotonic()
        if left <= 0:
            raise OutputsError("kompozitor neodpovedá")
        ready, _w, _x = select.select([self.sock], [], [], left)
        if not ready:
            raise OutputsError("kompozitor neodpovedá")
        try:
            data = self.sock.recv(65536)
        except OSError as err:
            raise OutputsError("spojenie s kompozitorom zlyhalo: %s" % err) from None
        if not data:
            raise OutputsError("spojenie s kompozitorom sa prerušilo")
        self.buf += data
        while len(self.buf) >= 8:
            obj, word = struct.unpack_from("=II", self.buf)
            size, opcode = word >> 16, word & 0xFFFF
            if len(self.buf) < size:
                break
            payload = bytes(self.buf[8:size])
            del self.buf[:size]
            self._dispatch(obj, opcode, payload)

    def roundtrip(self):
        """Počká, kým kompozitor spracuje všetko, čo sme poslali (a pošle, čo mu z toho vyplynie)."""
        callback = self._new_id()
        self.callbacks.add(callback)
        self._send(DISPLAY, DISPLAY_SYNC, struct.pack("=I", callback))
        deadline = time.monotonic() + self.timeout
        while callback in self.callbacks:
            self._pump(deadline)

    # ---------- udalosti ----------
    def _dispatch(self, obj, opcode, payload):
        if obj == DISPLAY:
            if opcode == DISPLAY_ERROR:
                _obj, code = struct.unpack_from("=II", payload)
                message, _ = _read_string(payload, 8)
                raise OutputsError("chyba protokolu %d: %s" % (code, message))
        elif obj in self.callbacks:
            self.callbacks.discard(obj)
        elif obj == self.registry:
            if opcode == REGISTRY_GLOBAL:
                (name,) = struct.unpack_from("=I", payload)
                iface, offset = _read_string(payload, 4)
                (version,) = struct.unpack_from("=I", payload, offset)
                if iface == MANAGER_IFACE and self.manager is None:
                    self.manager = self._bind(name, iface, min(version, MANAGER_VERSION))
        elif obj == self.manager:
            self._on_manager(opcode, payload)
        elif obj in self.heads:
            self._on_head(self.heads[obj], opcode, payload)
        elif obj in self.mode_owner:
            self._on_mode(self.mode_owner[obj], obj, opcode, payload)
        elif obj in self.result:
            self.result[obj] = opcode           # succeeded | failed | cancelled

    def _bind(self, name, iface, version):
        new_id = self._new_id()
        self._send(self.registry, REGISTRY_BIND,
                   struct.pack("=I", name) + _string(iface) + struct.pack("=II", version, new_id))
        return new_id

    def _on_manager(self, opcode, payload):
        if opcode == MGR_HEAD:
            (new_id,) = struct.unpack_from("=I", payload)
            self.heads[new_id] = Head(new_id)
        elif opcode == MGR_DONE:
            (self.serial,) = struct.unpack_from("=I", payload)
        elif opcode == MGR_FINISHED:
            raise OutputsError("kompozitor ukončil správu výstupov")

    def _on_head(self, head, opcode, payload):
        if opcode == H_NAME:
            head.name, _ = _read_string(payload, 0)
        elif opcode == H_DESCRIPTION:
            head.description, _ = _read_string(payload, 0)
        elif opcode == H_PHYSICAL_SIZE:
            head.width_mm, head.height_mm = struct.unpack_from("=ii", payload)
        elif opcode == H_MODE:
            (mode_id,) = struct.unpack_from("=I", payload)
            head.modes[mode_id] = Mode(mode_id)
            self.mode_owner[mode_id] = head
        elif opcode == H_ENABLED:
            (head.enabled,) = struct.unpack_from("=i", payload)
            head.enabled = bool(head.enabled)
        elif opcode == H_CURRENT_MODE:
            (head.current_mode,) = struct.unpack_from("=I", payload)
        elif opcode == H_POSITION:
            head.x, head.y = struct.unpack_from("=ii", payload)
        elif opcode == H_TRANSFORM:
            (head.transform,) = struct.unpack_from("=i", payload)
        elif opcode == H_SCALE:
            (raw,) = struct.unpack_from("=i", payload)
            head.scale = raw / 256.0
        elif opcode == H_FINISHED:
            head.finished = True
            self.heads.pop(head.id, None)
        elif opcode == H_MAKE:
            head.make, _ = _read_string(payload, 0)
        elif opcode == H_MODEL:
            head.model, _ = _read_string(payload, 0)
        elif opcode == H_SERIAL:
            head.serial, _ = _read_string(payload, 0)

    def _on_mode(self, head, mode_id, opcode, payload):
        mode = head.modes.get(mode_id)
        if mode is None:
            return
        if opcode == M_SIZE:
            mode.width, mode.height = struct.unpack_from("=ii", payload)
        elif opcode == M_REFRESH:
            (mode.refresh,) = struct.unpack_from("=i", payload)
        elif opcode == M_PREFERRED:
            mode.preferred = True
        elif opcode == M_FINISHED:
            head.modes.pop(mode_id, None)
            self.mode_owner.pop(mode_id, None)

    # ---------- čítanie a zmena ----------
    def monitors(self):
        return [h for h in self.heads.values() if not h.finished]

    def apply(self, changes, test_only=False):
        """Použije zmeny a vráti None, alebo text, prečo kompozitor zmenu odmietol.

        changes: {názov konektora: {"mode": (šírka, výška, refresh_mHz), "scale": 1.5,
                                     "transform": "normal"|"90"|..., "enabled": bool}}, všetky kľúče nepovinné.
        Monitory, ktoré zmena nespomína, ostanú tak, ako sú (do konfigurácie idú s aktuálnymi hodnotami).
        """
        unknown = set(changes) - {h.name for h in self.monitors()}
        if unknown:
            raise OutputsError("neznámy monitor: %s" % ", ".join(sorted(unknown)))
        cfg = self._new_id()
        self.result[cfg] = None
        self._send(self.manager, MGR_CREATE_CONFIGURATION, struct.pack("=II", cfg, self.serial or 0))
        head_objects = []
        for head in self.monitors():
            change = changes.get(head.name, {})
            if not change.get("enabled", head.enabled):
                self._send(cfg, CFG_DISABLE_HEAD, struct.pack("=I", head.id))
                continue
            entry = self._new_id()
            head_objects.append(entry)
            self._send(cfg, CFG_ENABLE_HEAD, struct.pack("=II", entry, head.id))
            self._set_mode(entry, head, change.get("mode"))
            self._send(entry, CH_SET_POSITION, struct.pack("=ii", head.x, head.y))
            transform = TRANSFORM_IDS[change["transform"]] if "transform" in change else head.transform
            self._send(entry, CH_SET_TRANSFORM, struct.pack("=i", transform))
            self._send(entry, CH_SET_SCALE, struct.pack("=i", _fixed(change.get("scale", head.scale))))
        self._send(cfg, CFG_TEST if test_only else CFG_APPLY)
        self.roundtrip()
        deadline = time.monotonic() + self.timeout
        while self.result[cfg] is None:
            self._pump(deadline)
        outcome = self.result.pop(cfg)
        for entry in head_objects:
            self._send(entry, CH_DESTROY)
        self._send(cfg, CFG_DESTROY)
        if outcome == CFG_SUCCEEDED:
            return None
        return ("kompozitor zmenu odmietol (nepodporovaný režim alebo monitor)" if outcome == CFG_FAILED
                else "zmena sa zrušila, lebo sa medzitým zmenilo zapojenie monitorov")

    def _set_mode(self, entry, head, wanted):
        if wanted is None:
            if head.current_mode in head.modes:
                self._send(entry, CH_SET_MODE, struct.pack("=I", head.current_mode))
            return
        width, height, refresh = wanted
        for mode in head.modes.values():
            if (mode.width, mode.height, mode.refresh) == (width, height, refresh):
                self._send(entry, CH_SET_MODE, struct.pack("=I", mode.id))
                return
        self._send(entry, CH_SET_CUSTOM_MODE, struct.pack("=iii", width, height, refresh))


def read():
    """Aktuálne monitory (zoznam Head). Vyhodí OutputsError, ak sa to nedá zistiť."""
    with Client() as client:
        heads = client.monitors()
    return sorted(heads, key=lambda h: h.id)


def apply(changes, test_only=False):
    """Krátke spojenie, zmena a zavretie. None = hotovo, inak text chyby."""
    with Client() as client:
        return client.apply(changes, test_only)
