import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gi.repository import GLib  # noqa: E402

from latte_appearance import portal  # noqa: E402
from latte_appearance.service import Service  # noqa: E402
from latte_common import appearance, settings  # noqa: E402


class FakeInvocation:
    def __init__(self):
        self.result = None
        self.error = None

    def return_value(self, value):
        self.result = value

    def return_dbus_error(self, name, message):
        self.error = (name, message)


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = self._tmp.name
        self.cfg = os.path.join(root, "cfg")
        self.dirs = appearance.Dirs(config_home=self.cfg, labwc=os.path.join(self.cfg, "labwc"))
        self.store = settings.Registry().store("appearance", directory=os.path.join(self.cfg, "latteos"), admin_dir=os.path.join(root, "admin"))
        self.reloads = 0
        self.service = Service(dirs=self.dirs, reload=self._reload, store=self.store)

    def tearDown(self):
        self._tmp.cleanup()

    def _reload(self):
        self.reloads += 1

    def test_first_enforce_writes_all_layers_and_reloads_compositor_once(self):
        changed = self.service.enforce()
        self.assertEqual(len(changed), len(appearance.plan(self.service.tokens, self.dirs)))
        self.assertEqual(self.reloads, 1)
        self.assertEqual(self.service.enforce(), [])
        self.assertEqual(self.reloads, 1)                    # nič sa nezmenilo: kompozitor sa nemení

    def test_setting_change_updates_files_and_portal(self):
        self.service.compute()
        self.service.enforce()
        before = self.reloads
        self.store.set("color.scheme", "light")
        self.service.on_change()
        text = open(os.path.join(self.dirs.labwc, "themerc-override"), encoding="utf-8").read()
        self.assertIn("light", text.splitlines()[0])
        self.assertEqual(self.reloads, before + 1)
        self.assertEqual(self.service.portal.values["org.freedesktop.appearance"]["color-scheme"], ("u", 2))

    def test_gtk_only_setting_does_not_reload_the_compositor(self):
        self.service.compute()
        self.service.enforce()
        before = self.reloads
        self.store.set("window.buttons", "close")
        self.service.on_change()
        self.assertEqual(self.reloads, before)

    def test_drift_is_repaired(self):
        self.service.compute()
        self.service.enforce()
        theme = os.path.join(self.dirs.labwc, "themerc-override")
        with open(theme, "w", encoding="utf-8") as f:
            f.write("window.active.title.bg.color: #FF0000\n")
        before = self.reloads
        self.service.on_drift()
        self.assertNotIn("FF0000", open(theme, encoding="utf-8").read())
        self.assertEqual(self.reloads, before + 1)

    def test_broken_settings_file_does_not_stop_enforcement(self):
        os.makedirs(os.path.dirname(self.store.path))
        with open(self.store.path, "w", encoding="utf-8") as f:
            f.write("[color\nscheme =")
        self.service.compute()
        self.assertTrue(any("appearance.toml" in p for p in self.service.tokens.problems))
        self.assertEqual(len(self.service.enforce()), len(appearance.plan(self.service.tokens, self.dirs)))      # predvolený vzhľad sa vynúti


class PortalUnitTest(unittest.TestCase):
    def setUp(self):
        self.state = {"scheme": 1}
        self.backend = portal.PortalBackend(self.provider)

    def provider(self):
        return {
            "org.freedesktop.appearance": {"color-scheme": ("u", self.state["scheme"]), "accent-color": ("(ddd)", (0.1, 0.2, 0.3))},
            "org.gnome.desktop.interface": {"color-scheme": ("s", "prefer-dark")},
        }

    def call(self, method, params):
        inv = FakeInvocation()
        self.backend._method_call(None, ":1.1", "/", "i", method, GLib.Variant.new_tuple(*params) if params else GLib.Variant("()", ()), inv)
        return inv

    def test_namespace_patterns(self):
        self.assertTrue(portal.namespace_matches("org.freedesktop.appearance", []))
        self.assertTrue(portal.namespace_matches("org.freedesktop.appearance", ["org.freedesktop.*"]))
        self.assertFalse(portal.namespace_matches("org.gnome.desktop.interface", ["org.freedesktop.*"]))
        self.assertTrue(portal.namespace_matches("org.gnome.desktop.interface", ["org.freedesktop.*", "org.gnome.*"]))

    def test_read_all_filters_by_namespace(self):
        everything = self.call("ReadAll", [GLib.Variant("as", [])]).result.unpack()[0]
        self.assertEqual(set(everything), {"org.freedesktop.appearance", "org.gnome.desktop.interface"})
        only = self.call("ReadAll", [GLib.Variant("as", ["org.freedesktop.*"])]).result.unpack()[0]
        self.assertEqual(set(only), {"org.freedesktop.appearance"})
        self.assertEqual(only["org.freedesktop.appearance"]["color-scheme"], 1)

    def test_read_one_and_not_found(self):
        got = self.call("ReadOne", [GLib.Variant("s", "org.freedesktop.appearance"), GLib.Variant("s", "color-scheme")])
        self.assertEqual(got.result.unpack(), (1,))
        legacy = self.call("Read", [GLib.Variant("s", "org.freedesktop.appearance"), GLib.Variant("s", "accent-color")])
        self.assertEqual(legacy.result.unpack()[0], (0.1, 0.2, 0.3))
        missing = self.call("ReadOne", [GLib.Variant("s", "org.freedesktop.appearance"), GLib.Variant("s", "nie-je")])
        self.assertEqual(missing.error[0], portal.NOT_FOUND)
        other = self.call("ReadOne", [GLib.Variant("s", "nie.je.namespace"), GLib.Variant("s", "x")])
        self.assertEqual(other.error[0], portal.NOT_FOUND)

    def test_refresh_reports_only_real_changes(self):
        self.assertEqual(self.backend.refresh(), 0)
        self.state["scheme"] = 2
        self.assertEqual(self.backend.refresh(), 1)
        self.assertEqual(self.backend.refresh(), 0)


@unittest.skipUnless(shutil.which("dbus-run-session"), "chýba dbus-run-session")
class PortalBusTest(unittest.TestCase):
    """Skutočné volania cez súkromnú session zbernicu (nie zbernicu používateľa).
    Backend a klient bežia v dvoch procesoch: synchrónne volanie v procese backendu by ho zablokovalo."""

    BACKEND = textwrap.dedent('''
        import json, sys
        sys.path.insert(0, %(src)r)
        from gi.repository import GLib
        from latte_appearance import portal

        def provider():
            try:
                scheme = json.load(open(%(state)r))["scheme"]
            except (OSError, ValueError, KeyError):
                scheme = 1
            return {"org.freedesktop.appearance": {"color-scheme": ("u", scheme)}}

        backend = portal.PortalBackend(provider)
        backend.start()
        GLib.timeout_add(100, lambda: (backend.refresh(), True)[1])
        GLib.MainLoop().run()
    ''')

    CLIENT = textwrap.dedent('''
        import json, sys
        sys.path.insert(0, %(src)r)
        from gi.repository import Gio, GLib
        from latte_appearance import portal

        proxy = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None,
                                               portal.BUS_NAME, portal.OBJECT_PATH, portal.INTERFACE, None)
        out = {"changed": []}
        out["version"] = proxy.get_cached_property("version").unpack()
        out["read_all"] = proxy.call_sync("ReadAll", GLib.Variant("(as)", ([],)), 0, 2000, None).unpack()[0]
        out["read_one"] = proxy.call_sync("ReadOne", GLib.Variant("(ss)", ("org.freedesktop.appearance", "color-scheme")), 0, 2000, None).unpack()[0]
        try:
            proxy.call_sync("ReadOne", GLib.Variant("(ss)", ("org.freedesktop.appearance", "nic")), 0, 2000, None)
        except GLib.Error as err:
            out["error"] = err.message
        proxy.connect("g-signal", lambda _p, _s, name, params: out["changed"].append([name, params.unpack()]))
        json.dump({"scheme": 2}, open(%(state)r, "w"))
        loop = GLib.MainLoop()
        GLib.timeout_add(1200, loop.quit)
        loop.run()
        print(json.dumps(out))
    ''')

    def test_real_calls_and_signal(self):
        src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
        with tempfile.TemporaryDirectory() as tmp:
            state = os.path.join(tmp, "state.json")
            backend, client = (os.path.join(tmp, n) for n in ("backend.py", "client.py"))
            for path, text in ((backend, self.BACKEND), (client, self.CLIENT)):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text % {"src": src, "state": state})
            shell = "%s %s & B=$!; sleep 1.5; %s %s; rc=$?; kill $B; exit $rc" % (
                sys.executable, backend, sys.executable, client)
            proc = subprocess.run(["dbus-run-session", "--", "sh", "-c", shell], capture_output=True, text=True, timeout=40)
        self.assertEqual(proc.returncode, 0, proc.stderr[-500:])
        out = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertEqual(out["version"], 2)
        self.assertEqual(out["read_all"]["org.freedesktop.appearance"]["color-scheme"], 1)
        self.assertEqual(out["read_one"], 1)
        self.assertIn("NotFound", out["error"])
        self.assertEqual(out["changed"], [["SettingChanged", ["org.freedesktop.appearance", "color-scheme", 2]]])


if __name__ == "__main__":
    unittest.main()
