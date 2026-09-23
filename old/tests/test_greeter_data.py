import os
import pwd
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_greeter import sessions, state, users  # noqa: E402


def entry(name, gecos, uid, shell="/bin/bash"):
    return pwd.struct_passwd((name, "x", uid, uid, gecos, "/home/" + name, shell))


class UsersTest(unittest.TestCase):
    ENTRIES = [
        entry("root", "root", 0),
        entry("greetd", "greetd daemon", 982, "/usr/sbin/nologin"),
        entry("nobody", "Kernel Overflow User", 65534, "/sbin/nologin"),
        entry("zita", "Zita Nováková,,,", 1001),
        entry("arkay", "Arkay", 1000),
        entry("ftp", "FTP", 1002, "/sbin/nologin"),
    ]

    def test_only_login_accounts_and_real_name_from_gecos(self):
        found = users.list_users(entries=self.ENTRIES, icons_dir="/nonexistent")
        self.assertEqual([u.name for u in found], ["arkay", "zita"])
        self.assertEqual(found[1].title, "Zita Nováková")

    def test_recent_users_come_first(self):
        found = users.list_users(recent=["zita"], entries=self.ENTRIES, icons_dir="/nonexistent")
        self.assertEqual([u.name for u in found], ["zita", "arkay"])

    def test_avatar_only_when_readable_file_exists(self):
        with tempfile.TemporaryDirectory() as icons:
            open(os.path.join(icons, "zita"), "wb").close()
            found = {u.name: u for u in users.list_users(entries=self.ENTRIES, icons_dir=icons)}
        self.assertEqual(found["zita"].avatar, os.path.join(icons, "zita"))
        self.assertIsNone(found["arkay"].avatar)


class StateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LATTEOS_GREETER_STATE"] = os.path.join(self._tmp.name, "sub", "greeter.json")

    def tearDown(self):
        del os.environ["LATTEOS_GREETER_STATE"]
        self._tmp.cleanup()

    def test_roundtrip_and_recency(self):
        s = state.State.load()
        self.assertIsNone(s.last_user)
        s.record_login("arkay", "LatteOS")
        s.record_login("zita", "Konzola (headless)")
        s.record_login("arkay", "LatteOS")
        again = state.State.load()
        self.assertEqual(again.recent, ["arkay", "zita"])
        self.assertEqual(again.last_user, "arkay")
        self.assertEqual(again.sessions["zita"], "Konzola (headless)")

    def test_garbage_file_gives_empty_state(self):
        os.makedirs(os.path.dirname(state.state_file()))
        with open(state.state_file(), "w") as f:
            f.write("{nie json")
        self.assertEqual(state.State.load().recent, [])


class SessionsTest(unittest.TestCase):
    def write(self, directory, name, body):
        with open(os.path.join(directory, name), "w") as f:
            f.write(body)

    def test_latteos_first_hidden_skipped_console_only_in_dev(self):
        with tempfile.TemporaryDirectory() as d:
            self.write(d, "a-sway.desktop", "[Desktop Entry]\nName=Sway\nExec=sway\n")
            self.write(d, "latteos.desktop", "[Desktop Entry]\nName=LatteOS\nExec=latteos-session\n")
            self.write(d, "skryta.desktop", "[Desktop Entry]\nName=X\nExec=x\nNoDisplay=true\n")
            self.write(d, "rozbita.desktop", "toto nie je desktop súbor")
            dev = sessions.load(d, dev=True)
            release = sessions.load(d, dev=False)
        self.assertEqual([s.name for s in dev], ["LatteOS", "Sway", "Konzola (headless)"])
        self.assertEqual([s.name for s in release], ["LatteOS", "Sway"])
        self.assertEqual(dev[0].cmd, ["latteos-session"])

    def test_no_sessions_installed_still_offers_latteos(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(sessions.load(d, dev=False)[0].cmd, ["latteos-session"])


if __name__ == "__main__":
    unittest.main()
