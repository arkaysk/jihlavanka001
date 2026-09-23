"""Skript session/latteos-session: ako zaznamená skončenie labwc (bod 2b.5)."""
import os
import stat
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import lastexit  # noqa: E402

SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "session")

FAKE_LABWC = """#!/bin/sh
case "$FAKE" in
    segv) kill -SEGV $$ ;;
    kill) kill -KILL $$ ;;
    term) kill -TERM $$ ;;
    *) exit "${FAKE:-0}" ;;
esac
"""


def script(path, text):
    with open(path, "w") as f:
        f.write(text)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)


class SessionScriptTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.bin)
        os.makedirs(os.path.join(self.tmp, "home"))
        self.shared = os.path.join(self.tmp, "shared")
        os.makedirs(self.shared)
        script(os.path.join(self.bin, "labwc"), FAKE_LABWC)
        script(os.path.join(self.bin, "systemd-cat"), '#!/bin/sh\nshift 2\nexec "$@"\n')
        script(os.path.join(self.bin, "systemctl"), "#!/bin/sh\nexit 0\n")
        # logger nezapisuje do skutočného journalu, len si poznačí správu
        script(os.path.join(self.bin, "logger"),
               '#!/bin/sh\ncat >> "%s/journal"\n' % self.tmp)
        os.symlink(os.path.join(SESSION_DIR, "latteos-diag"), os.path.join(self.bin, "latteos-diag"))
        self.user = subprocess.run(["id", "-un"], capture_output=True, text=True).stdout.strip()

    def tearDown(self):
        self._tmp.cleanup()

    def env(self, **extra):
        env = {
            "PATH": self.bin + ":/usr/bin:/bin",
            "HOME": os.path.join(self.tmp, "home"),
            "LATTEOS_STATE_DIR": self.shared,
            "XDG_STATE_HOME": os.path.join(self.tmp, "state"),
        }
        env.update(extra)
        return env

    def run_session(self, fake):
        return subprocess.run(
            ["/bin/sh", os.path.join(SESSION_DIR, "latteos-session")],
            env=self.env(FAKE=fake), capture_output=True, text=True,
        )

    def shared_record(self):
        return lastexit.read(self.user, self.shared)

    def journal(self):
        with open(os.path.join(self.tmp, "journal")) as f:
            return f.read()

    def test_normal_exit_leaves_no_problem_record(self):
        result = self.run_session("0")
        self.assertEqual(result.returncode, 0)
        self.assertIsNone(self.shared_record())
        self.assertNotIn("Diagnostika", result.stderr)

    def test_sigterm_from_outside_is_not_a_crash(self):
        result = self.run_session("term")
        self.assertEqual(result.returncode, 143)
        self.assertIsNone(self.shared_record())

    def test_segv_is_a_crash_and_is_reported_everywhere(self):
        result = self.run_session("segv")
        self.assertEqual(result.returncode, 139)
        record = self.shared_record()
        self.assertEqual((record.kind, record.signal, record.status), ("crash", "SEGV", 139))
        self.assertIn("LATTEOS_KIND=crash", self.journal())
        self.assertIn("latteos-diag", result.stderr)

    def test_sigkill_is_reported_as_killed(self):
        self.run_session("kill")
        self.assertEqual(self.shared_record().kind, "killed")

    def test_error_exit_code(self):
        self.run_session("1")
        record = self.shared_record()
        self.assertEqual((record.kind, record.status, record.signal), ("error", 1, ""))

    def test_missing_labwc(self):
        self.run_session("127")
        self.assertEqual(self.shared_record().kind, "missing")

    def test_new_session_clears_previous_crash_for_the_greeter(self):
        self.run_session("segv")
        self.assertIsNotNone(self.shared_record())
        self.run_session("0")
        self.assertIsNone(self.shared_record())

    def test_record_is_readable_by_the_greeter_user(self):
        self.run_session("segv")
        mode = os.stat(os.path.join(self.shared, self.user)).st_mode
        self.assertTrue(mode & stat.S_IROTH)

    def test_unwritable_shared_dir_does_not_break_the_session(self):
        result = subprocess.run(
            ["/bin/sh", os.path.join(SESSION_DIR, "latteos-session")],
            env=self.env(FAKE="segv", LATTEOS_STATE_DIR="/proc/nonexistent/dir"),
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 139)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, "state", "latteos", "last-exit")))

    def test_diag_notice_only_after_a_problem(self):
        self.run_session("0")
        quiet = subprocess.run(["/bin/sh", os.path.join(SESSION_DIR, "latteos-diag"), "notice"],
                               env=self.env(), capture_output=True, text=True)
        self.assertEqual(quiet.stdout, "")
        self.run_session("segv")
        loud = subprocess.run(["/bin/sh", os.path.join(SESSION_DIR, "latteos-diag"), "notice"],
                              env=self.env(), capture_output=True, text=True)
        self.assertIn("spadla", loud.stdout)
        self.assertIn("SEGV", loud.stdout)


if __name__ == "__main__":
    unittest.main()
