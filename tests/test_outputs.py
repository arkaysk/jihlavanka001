import os
import socket
import struct
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import outputs  # noqa: E402

HEAD, MODE_BIG, MODE_SMALL = 0xFF000001, 0xFF000002, 0xFF000003


def message(obj, opcode, payload=b""):
    return struct.pack("=II", obj, ((8 + len(payload)) << 16) | opcode) + payload


class FakeCompositor(threading.Thread):
    """Minimálny kompozitor s jedným monitorom (LG 27GL850, dva režimy). Zapisuje všetky povely klienta."""

    def __init__(self, path, outcome=0, advertise=True, protocol_error=False, silent=False):
        super().__init__(daemon=True)
        self.outcome = outcome              # 0 succeeded, 1 failed, 2 cancelled
        self.advertise = advertise
        self.protocol_error = protocol_error
        self.silent = silent
        self.requests = []                  # (objekt, opcode, payload)
        self.registry = self.manager = None
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(path)
        self.server.listen(1)
        self.stop = threading.Event()

    def run(self):
        self.server.settimeout(2)
        try:
            conn, _ = self.server.accept()
        except OSError:
            return
        with conn:
            conn.settimeout(0.1)
            buf = b""
            try:
                while not self.stop.is_set():
                    try:
                        data = conn.recv(65536)
                    except socket.timeout:
                        continue
                    if not data:
                        break
                    buf += data
                    while len(buf) >= 8:
                        obj, word = struct.unpack_from("=II", buf)
                        size, opcode = word >> 16, word & 0xFFFF
                        if len(buf) < size:
                            break
                        payload, buf = buf[8:size], buf[size:]
                        self.requests.append((obj, opcode, payload))
                        if not self.silent:
                            conn.sendall(self.handle(obj, opcode, payload))
            except OSError:
                pass                        # klient sa odpojil (napr. po chybe protokolu)

    def close(self):
        self.stop.set()
        self.join(timeout=3)
        self.server.close()

    def handle(self, obj, opcode, payload):
        s = outputs._string
        out = b""
        if obj == 1 and opcode == 1:                                  # get_registry
            (self.registry,) = struct.unpack("=I", payload)
            if self.advertise:
                out += message(self.registry, 0, struct.pack("=I", 1) + s(outputs.MANAGER_IFACE) + struct.pack("=I", 4))
        elif obj == 1 and opcode == 0:                                # sync
            (cb,) = struct.unpack("=I", payload)
            out += message(cb, 0, struct.pack("=I", 0))
        elif obj == self.registry and opcode == 0:                    # bind
            _name, offset = struct.unpack_from("=I", payload)[0], 4
            _iface, offset = outputs._read_string(payload, offset)
            (_version, self.manager) = struct.unpack_from("=II", payload, offset)
            if self.protocol_error:
                out += message(1, 0, struct.pack("=II", self.manager, 7) + s("zlé použitie"))
                return out
            out += message(self.manager, outputs.MGR_HEAD, struct.pack("=I", HEAD))
            out += message(HEAD, outputs.H_NAME, s("HDMI-A-1"))
            out += message(HEAD, outputs.H_DESCRIPTION, s("LG Electronics 27GL850"))
            out += message(HEAD, outputs.H_PHYSICAL_SIZE, struct.pack("=ii", 597, 336))
            for mode_id, w, h, hz, pref in ((MODE_BIG, 2560, 1440, 143912, True), (MODE_SMALL, 1920, 1080, 60000, False)):
                out += message(HEAD, outputs.H_MODE, struct.pack("=I", mode_id))
                out += message(mode_id, outputs.M_SIZE, struct.pack("=ii", w, h))
                out += message(mode_id, outputs.M_REFRESH, struct.pack("=i", hz))
                if pref:
                    out += message(mode_id, outputs.M_PREFERRED)
            out += message(HEAD, outputs.H_ENABLED, struct.pack("=i", 1))
            out += message(HEAD, outputs.H_CURRENT_MODE, struct.pack("=I", MODE_BIG))
            out += message(HEAD, outputs.H_POSITION, struct.pack("=ii", 0, 0))
            out += message(HEAD, outputs.H_TRANSFORM, struct.pack("=i", 0))
            out += message(HEAD, outputs.H_SCALE, struct.pack("=i", 256))
            out += message(HEAD, outputs.H_MAKE, s("LG Electronics"))
            out += message(HEAD, outputs.H_MODEL, s("27GL850"))
            out += message(HEAD, outputs.H_SERIAL, s("123456"))
            out += message(self.manager, outputs.MGR_DONE, struct.pack("=I", 7))
        elif opcode in (outputs.CFG_APPLY, outputs.CFG_TEST) and obj > 3 and self.is_configuration(obj):
            out += message(obj, self.outcome)
        return out

    def is_configuration(self, obj):
        return any(o == self.manager and c == outputs.MGR_CREATE_CONFIGURATION and struct.unpack("=I", p[:4])[0] == obj
                   for o, c, p in self.requests)

    def commands_after_create(self):
        """Povely konfigurácie ako (opcode, argumenty) v poradí, v akom prišli."""
        names = {outputs.CFG_ENABLE_HEAD: "enable_head", outputs.CFG_DISABLE_HEAD: "disable_head",
                 outputs.CFG_APPLY: "apply", outputs.CFG_TEST: "test"}
        head_names = {outputs.CH_SET_MODE: "set_mode", outputs.CH_SET_CUSTOM_MODE: "set_custom_mode",
                      outputs.CH_SET_POSITION: "set_position", outputs.CH_SET_TRANSFORM: "set_transform",
                      outputs.CH_SET_SCALE: "set_scale"}
        created = [(o, p) for o, c, p in self.requests if o == self.manager and c == outputs.MGR_CREATE_CONFIGURATION]
        if not created:
            return None, []
        cfg = struct.unpack("=I", created[0][1][:4])[0]
        serial = struct.unpack("=I", created[0][1][4:8])[0]
        entries, out = set(), []
        for obj, opcode, payload in self.requests:
            if obj == cfg and opcode in names:
                if opcode == outputs.CFG_ENABLE_HEAD:
                    entries.add(struct.unpack("=I", payload[:4])[0])
                out.append((names[opcode], payload))
            elif obj in entries and opcode in head_names:
                fields = {"set_mode": "=I", "set_custom_mode": "=iii", "set_position": "=ii", "set_transform": "=i",
                          "set_scale": "=i"}[head_names[opcode]]
                out.append((head_names[opcode], struct.unpack(fields, payload)))
        return serial, out


class OutputsClientTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.path = os.path.join(self._tmp, "wl")
        self._env = os.environ.get("WAYLAND_DISPLAY")
        os.environ["WAYLAND_DISPLAY"] = self.path

    def tearDown(self):
        if self._env is None:
            os.environ.pop("WAYLAND_DISPLAY", None)
        else:
            os.environ["WAYLAND_DISPLAY"] = self._env
        if getattr(self, "server", None):
            self.server.close()
        try:
            os.unlink(self.path)
        except OSError:
            pass
        os.rmdir(self._tmp)

    def start(self, **kw):
        self.server = FakeCompositor(self.path, **kw)
        self.server.start()
        return self.server

    def test_reads_monitors_with_modes_and_edid_identity(self):
        self.start()
        (head,) = outputs.read()
        self.assertEqual((head.name, head.make, head.model, head.serial), ("HDMI-A-1", "LG Electronics", "27GL850", "123456"))
        self.assertEqual((head.width_mm, head.height_mm, head.enabled, head.scale), (597, 336, True, 1.0))
        self.assertEqual(sorted((m.width, m.height, m.refresh, m.preferred) for m in head.modes.values()),
                         [(1920, 1080, 60000, False), (2560, 1440, 143912, True)])
        current = head.current
        self.assertEqual((current.width, current.height, current.refresh), (2560, 1440, 143912))

    def test_apply_sends_a_complete_configuration(self):
        server = self.start()
        error = outputs.apply({"HDMI-A-1": {"mode": (1920, 1080, 60000), "scale": 1.5, "transform": "90"}})
        self.assertIsNone(error)
        serial, commands = server.commands_after_create()
        self.assertEqual(serial, 7)                      # sériové číslo stavu, ktorý klient videl
        self.assertEqual([c for c, _a in commands],
                         ["enable_head", "set_mode", "set_position", "set_transform", "set_scale", "apply"])
        args = dict(commands)
        self.assertEqual(args["set_mode"], (MODE_SMALL,))
        self.assertEqual(args["set_position"], (0, 0))
        self.assertEqual(args["set_transform"], (1,))
        self.assertEqual(args["set_scale"], (384,))      # 1,5 vo formáte fixed 24.8

    def test_untouched_settings_are_sent_with_their_current_values(self):
        server = self.start()
        outputs.apply({"HDMI-A-1": {"scale": 2.0}})
        args = dict(server.commands_after_create()[1])
        self.assertEqual(args["set_mode"], (MODE_BIG,))
        self.assertEqual(args["set_transform"], (0,))

    def test_mode_the_monitor_does_not_list_is_sent_as_custom(self):
        server = self.start()
        outputs.apply({"HDMI-A-1": {"mode": (1024, 768, 60000)}})
        self.assertEqual(dict(server.commands_after_create()[1])["set_custom_mode"], (1024, 768, 60000))

    def test_disabling_a_monitor(self):
        server = self.start()
        outputs.apply({"HDMI-A-1": {"enabled": False}})
        self.assertEqual([c for c, _a in server.commands_after_create()[1]], ["disable_head", "apply"])

    def test_test_only_does_not_apply(self):
        server = self.start()
        self.assertIsNone(outputs.apply({"HDMI-A-1": {"scale": 2.0}}, test_only=True))
        commands = [c for c, _a in server.commands_after_create()[1]]
        self.assertIn("test", commands)
        self.assertNotIn("apply", commands)

    def test_refusal_and_cancellation_come_back_as_text(self):
        self.start(outcome=outputs.CFG_FAILED)
        self.assertIn("odmietol", outputs.apply({"HDMI-A-1": {"scale": 2.0}}))
        self.server.close()
        os.unlink(self.path)
        self.start(outcome=outputs.CFG_CANCELLED)
        self.assertIn("zrušila", outputs.apply({"HDMI-A-1": {"scale": 2.0}}))

    def test_unknown_monitor_is_refused_before_anything_is_sent(self):
        server = self.start()
        with self.assertRaises(outputs.OutputsError):
            outputs.apply({"DP-9": {"scale": 2.0}})
        self.assertEqual(server.commands_after_create(), (None, []))

    def test_compositor_without_the_protocol(self):
        self.start(advertise=False)
        with self.assertRaises(outputs.OutputsError) as ctx:
            outputs.read()
        self.assertIn("nepodporuje", str(ctx.exception))

    def test_protocol_error_is_raised_with_the_compositor_message(self):
        self.start(protocol_error=True)
        with self.assertRaises(outputs.OutputsError) as ctx:
            outputs.read()
        self.assertIn("zlé použitie", str(ctx.exception))

    def test_silent_compositor_times_out(self):
        self.start(silent=True)
        with self.assertRaises(outputs.OutputsError) as ctx:
            outputs.Client(timeout=0.3).connect()
        self.assertIn("neodpovedá", str(ctx.exception))

    def test_missing_session(self):
        os.environ.pop("WAYLAND_DISPLAY")
        with self.assertRaises(outputs.OutputsError) as ctx:
            outputs.read()
        self.assertIn("WAYLAND_DISPLAY", str(ctx.exception))

    def test_socket_that_does_not_exist(self):
        os.environ["WAYLAND_DISPLAY"] = os.path.join(self._tmp, "nie-je")
        with self.assertRaises(outputs.OutputsError):
            outputs.read()


if __name__ == "__main__":
    unittest.main()
