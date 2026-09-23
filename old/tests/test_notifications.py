import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gi.repository import Gio, GLib  # noqa: E402

from latte_shell import notify_center as nc  # noqa: E402
from latte_shell import notify_service  # noqa: E402


def make(center, app="app", replaces=0, summary="Nadpis", body="Text", actions=None, hints=None,
         timeout=-1):
    return center.notify(app, replaces, "", summary, body, actions or [], hints or {}, timeout)


class CenterTest(unittest.TestCase):
    def setUp(self):
        self.c = nc.Center()
        self.events = []
        self.c.on_popup = lambda n: self.events.append(("popup", n.id))
        self.c.on_popup_close = lambda i: self.events.append(("popup-close", i))
        self.c.on_closed = lambda i, r: self.events.append(("closed", i, r))
        self.c.on_action = lambda i, k: self.events.append(("action", i, k))

    def test_ids_start_at_one_and_grow(self):
        self.assertEqual([make(self.c), make(self.c)], [1, 2])

    def test_replacing_keeps_the_id_and_the_list_size(self):
        first = make(self.c, summary="a")
        again = make(self.c, replaces=first, summary="b")
        self.assertEqual(again, first)
        self.assertEqual([n.summary for n in self.c.items], ["b"])

    def test_replacing_an_unknown_id_creates_a_new_notification(self):
        self.assertEqual(make(self.c, replaces=99), 1)

    def test_newest_comes_first(self):
        make(self.c, summary="stará")
        make(self.c, summary="nová")
        self.assertEqual([n.summary for n in self.c.items], ["nová", "stará"])

    def test_actions_come_as_key_text_pairs(self):
        make(self.c, actions=["default", "Otvoriť", "del", "Zmazať"])
        self.assertEqual(self.c.items[0].actions, [("default", "Otvoriť"), ("del", "Zmazať")])

    def test_timeouts(self):
        make(self.c)
        make(self.c, timeout=0)
        make(self.c, timeout=1500)
        make(self.c, hints={"urgency": 2}, timeout=1500)
        self.assertEqual([n.timeout_ms for n in reversed(self.c.items)],
                         [nc.DEFAULT_TIMEOUT_MS, 0, 1500, 0])      # kritické nevyprší

    def test_bad_urgency_is_normal(self):
        make(self.c, hints={"urgency": "vysoka"})
        self.assertEqual(self.c.items[0].urgency, nc.URGENCY_NORMAL)

    def test_expired_popup_stays_in_the_list(self):
        nid = make(self.c)
        self.c.popup_expired(nid)
        self.assertEqual(self.c.count, 1)
        self.assertFalse(self.c.items[0].popup)
        self.assertIn(("closed", nid, nc.CLOSED_EXPIRED), self.events)

    def test_transient_notification_vanishes_with_its_popup(self):
        nid = make(self.c, hints={"transient": True})
        self.c.popup_expired(nid)
        self.assertEqual(self.c.count, 0)

    def test_dismissing_removes_it_and_tells_the_app(self):
        nid = make(self.c)
        self.assertTrue(self.c.close(nid))
        self.assertEqual(self.c.count, 0)
        self.assertIn(("closed", nid, nc.CLOSED_DISMISSED), self.events)
        self.assertFalse(self.c.close(nid))

    def test_invoking_an_action_tells_the_app_then_closes(self):
        nid = make(self.c, actions=["ok", "Dobre"])
        self.c.invoke(nid, "ok")
        self.assertEqual([e for e in self.events if e[0] in ("action", "closed")],
                         [("action", nid, "ok"), ("closed", nid, nc.CLOSED_DISMISSED)])

    def test_do_not_disturb_keeps_notifications_but_shows_no_popup(self):
        self.c.set_dnd(True)
        nid = make(self.c)
        self.assertFalse(self.c.find(nid).popup)
        self.assertNotIn(("popup", nid), self.events)
        self.assertEqual(self.c.count, 1)

    def test_do_not_disturb_lets_critical_through(self):
        self.c.set_dnd(True)
        nid = make(self.c, hints={"urgency": 2})
        self.assertIn(("popup", nid), self.events)

    def test_turning_on_do_not_disturb_hides_open_popups(self):
        nid = make(self.c)
        self.c.set_dnd(True)
        self.assertIn(("popup-close", nid), self.events)
        self.assertEqual(self.c.count, 1)

    def test_history_is_limited(self):
        for _ in range(nc.HISTORY_LIMIT + 5):
            make(self.c)
        self.assertEqual(self.c.count, nc.HISTORY_LIMIT)

    def test_clear_closes_everything(self):
        make(self.c)
        make(self.c)
        self.c.clear()
        self.assertEqual(self.c.count, 0)


class ServiceTest(unittest.TestCase):
    """Skutočné volania D-Bus cez priame spojenie (bez zbernice, tá v testoch nie je)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.center = nc.Center()
        self.service = notify_service.Service(self.center)
        self.server_side = []
        self.server = Gio.DBusServer.new_sync(
            "unix:tmpdir=" + self._tmp.name, Gio.DBusServerFlags.AUTHENTICATION_ALLOW_ANONYMOUS,
            Gio.dbus_generate_guid(), None, None)
        self.server.connect("new-connection", self.on_connection)
        self.server.start()
        self.client = None
        Gio.DBusConnection.new_for_address(
            self.server.get_client_address(), Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT,
            None, None, self.connected)
        self.wait(lambda: self.client is not None)
        self.signals = []
        self.client.signal_subscribe(None, notify_service.NAME, None, notify_service.PATH, None,
                                     Gio.DBusSignalFlags.NONE, self.on_signal)

    def tearDown(self):
        self.client.close_sync(None)
        self.server.stop()
        self._tmp.cleanup()

    def on_connection(self, _server, connection):
        self.server_side.append(connection)
        self.service.export(connection)
        return True

    def connected(self, _src, result):
        self.client = Gio.DBusConnection.new_for_address_finish(result)

    def on_signal(self, _c, _s, _p, _i, name, params):
        self.signals.append((name, params.unpack()))

    def wait(self, done, seconds=5):
        context = GLib.MainContext.default()
        deadline = GLib.get_monotonic_time() + seconds * 1_000_000
        while not done():
            if GLib.get_monotonic_time() > deadline:
                self.fail("čakanie na D-Bus vypršalo")
            context.iteration(False)

    def call(self, method, params=None, reply="*"):
        box = []
        self.client.call(None, notify_service.PATH, notify_service.NAME, method, params,
                         GLib.VariantType(reply), Gio.DBusCallFlags.NONE, 5000, None,
                         lambda c, r: box.append(self._finish(c, r)))
        self.wait(lambda: box)
        if isinstance(box[0], GLib.Error):
            raise box[0]
        return box[0].unpack()

    @staticmethod
    def _finish(conn, result):
        try:
            return conn.call_finish(result)
        except GLib.Error as err:
            return err

    def notify(self, summary="Ahoj", **kw):
        args = ("app", kw.get("replaces", 0), "", summary, kw.get("body", ""),
                kw.get("actions", []), kw.get("hints", {}), kw.get("timeout", -1))
        return self.call("Notify", GLib.Variant("(susssasa{sv}i)", args))[0]

    def test_server_information_and_capabilities(self):
        self.assertEqual(self.call("GetServerInformation")[0], "latte-shell")
        self.assertEqual(self.call("GetCapabilities")[0], ["body", "actions"])

    def test_notify_reaches_the_center_and_returns_an_id(self):
        nid = self.notify("Nadpis", body="Telo", actions=["default", "Otvoriť"],
                          hints={"urgency": GLib.Variant("y", 2)})
        note = self.center.find(nid)
        self.assertEqual((note.summary, note.body, note.urgency), ("Nadpis", "Telo", 2))
        self.assertEqual(note.actions, [("default", "Otvoriť")])

    def test_close_notification_emits_the_closed_signal_with_reason_three(self):
        nid = self.notify()
        self.call("CloseNotification", GLib.Variant("(u)", (nid,)), "()")
        self.wait(lambda: self.signals)
        self.assertEqual(self.signals[-1], ("NotificationClosed", (nid, 3)))
        self.assertEqual(self.center.count, 0)

    def test_dismissing_emits_reason_two_and_action_emits_action_invoked(self):
        nid = self.notify(actions=["ok", "Dobre"])
        self.center.invoke(nid, "ok")
        self.wait(lambda: len(self.signals) >= 2)
        self.assertEqual(self.signals[:2], [("ActionInvoked", (nid, "ok")),
                                            ("NotificationClosed", (nid, 2))])

    def test_unknown_method_is_an_error_not_a_crash(self):
        with self.assertRaises(GLib.Error):
            self.call("Neexistuje")
        self.assertEqual(self.notify("po chybe"), 1)


if __name__ == "__main__":
    unittest.main()
