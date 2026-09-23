"""Skript session/latteos-logout: poradie krokov pri odhlásení a vypnutí (podvrhnuté príkazy)."""
import os
import stat
import subprocess
import tempfile
import unittest

HELPER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "session", "latteos-logout")
ME = subprocess.run(["id", "-un"], capture_output=True, text=True).stdout.strip()


def script(path, text):
    with open(path, "w") as f:
        f.write(text)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)


class LogoutHelperTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.bin)
        self.log = os.path.join(self.tmp, "calls")
        # každý podvrhnutý príkaz si zapíše volanie; správanie riadia premenné prostredia
        script(os.path.join(self.bin, "labwc"),
               '#!/bin/sh\necho "labwc $*" >> "%s"\nexit "${LABWC_RC:-0}"\n' % self.log)
        script(os.path.join(self.bin, "logger"), '#!/bin/sh\necho "logger $*" >> "%s"\n' % self.log)
        script(os.path.join(self.bin, "loginctl"), """#!/bin/sh
echo "loginctl $*" >> "%s"
case "$1" in
    show-session) case "$4" in Service) echo "${SVC:-greetd}" ;; Name) echo "${NAME:-%s}" ;; esac ;;
esac
""" % (self.log, ME))
        # is-active: cieľ relácie je "aktívny", kým sa nevyčerpá TARGET_BUSY volaní
        script(os.path.join(self.bin, "systemctl"), """#!/bin/sh
echo "systemctl $*" >> "%(log)s"
case "$*" in
    "--user is-active --quiet latte-session.target")
        n=$(cat "%(tmp)s/busy" 2>/dev/null || echo "${TARGET_BUSY:-0}")
        if [ "$n" -gt 0 ]; then echo $((n - 1)) > "%(tmp)s/busy"; exit 0; fi
        exit 3 ;;
    "is-active --quiet greetd") [ -n "$GREETD" ] && exit 0; exit 3 ;;
    isolate*) exit "${ISOLATE_RC:-0}" ;;
esac
""" % {"log": self.log, "tmp": self.tmp})

    def tearDown(self):
        self._tmp.cleanup()

    def run_helper(self, *args, **env_extra):
        env = {
            "PATH": self.bin + ":/usr/bin:/bin",
            "LABWC_PID": "99999999",          # neexistuje: labwc "už skončil"
            "XDG_SESSION_ID": "5",
        }
        env.update(env_extra)
        for key in [k for k, v in env.items() if v is None]:
            del env[key]
        return subprocess.run(["/bin/sh", HELPER, *args], env=env, capture_output=True, text=True)

    def calls(self):
        try:
            with open(self.log) as f:
                return f.read().splitlines()
        except FileNotFoundError:
            return []

    def test_logout_exits_labwc_cleanly_then_ends_the_greetd_login(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        self.assertEqual(calls[0], "labwc --exit")
        self.assertIn("loginctl terminate-session 5", calls)
        self.assertLess(calls.index("labwc --exit"), calls.index("loginctl terminate-session 5"))
        self.assertFalse([c for c in calls if c.startswith("systemctl isolate")])

    def test_login_not_owned_by_greetd_is_left_alone(self):
        self.run_helper(SVC="sshd")
        self.assertNotIn("loginctl terminate-session 5", self.calls())

    def test_session_of_another_user_is_left_alone(self):
        self.run_helper(NAME="nikto-iny")
        self.assertNotIn("loginctl terminate-session 5", self.calls())

    def test_waits_for_the_session_cleanup_before_ending_the_login(self):
        self.run_helper(TARGET_BUSY="3")
        active_checks = [c for c in self.calls() if c.endswith("is-active --quiet latte-session.target")]
        self.assertEqual(len(active_checks), 4)          # 3x aktívny, 4. raz už nie
        self.assertIn("loginctl terminate-session 5", self.calls())

    def test_console_switches_to_text_mode_when_greetd_runs(self):
        result = self.run_helper("--console", GREETD="1")
        self.assertEqual(result.returncode, 0)
        calls = self.calls()
        self.assertIn("systemctl isolate --no-ask-password multi-user.target", calls)
        self.assertNotIn("loginctl terminate-session 5", calls)     # isolate to už vyriešil

    def test_console_falls_back_to_login_screen_when_isolate_is_refused(self):
        self.run_helper("--console", GREETD="1", ISOLATE_RC="1")
        calls = self.calls()
        self.assertTrue([c for c in calls if c.startswith("logger ")])
        self.assertIn("loginctl terminate-session 5", calls)

    def test_console_without_greetd_does_not_isolate(self):
        self.run_helper("--console")
        self.assertFalse([c for c in self.calls() if c.startswith("systemctl isolate")])

    def test_without_labwc_pid_it_does_nothing(self):
        result = self.run_helper(LABWC_PID=None)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.calls(), [])

    def test_failed_labwc_exit_ends_nothing(self):
        result = self.run_helper(LABWC_RC="1")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("loginctl terminate-session 5", self.calls())


if __name__ == "__main__":
    unittest.main()
