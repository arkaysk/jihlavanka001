import os
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
SCRIPT = os.path.join(ROOT, "tools", "create-users.sh")

# Falošné príkazy: skript sa nikdy nespúšťa naozaj ako root. `id -u` hlási 0 a všetko ostatné sa len zapíše.
STUBS = {
    "id": '''#!/bin/sh
if [ "$1" = "-u" ]; then echo 0; exit 0; fi
grep -qx "$1" "$STATE/existing" 2>/dev/null
''',
    "useradd": '#!/bin/sh\necho "useradd $*" >> "$STATE/log"\n',
    "getent": '#!/bin/sh\necho "$2:x:1001:1001::/home/$2:/bin/bash"\n',
    "chmod": '#!/bin/sh\necho "chmod $*" >> "$STATE/log"\n',
    "install": '#!/bin/sh\necho "install $*" >> "$STATE/log"\n',
    "restorecon": '#!/bin/sh\necho "restorecon $*" >> "$STATE/log"\n',
    "passwd": '''#!/bin/sh
if [ "$1" = "-S" ]; then echo "$2 LK 2026-09-20 0 99999 7 -1"; exit 0; fi
echo "passwd $*" >> "$STATE/log"
''',
}


class CreateUsersScriptTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.state = self._tmp.name
        self.bin = os.path.join(self.state, "bin")
        os.makedirs(self.bin)
        for name, body in STUBS.items():
            path = os.path.join(self.bin, name)
            with open(path, "w") as f:
                f.write(body)
            os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
        self.log = os.path.join(self.state, "log")

    def tearDown(self):
        self._tmp.cleanup()

    def run_script(self, existing=(), env_extra=None, as_root=True):
        with open(os.path.join(self.state, "existing"), "w") as f:
            f.write("\n".join(existing) + "\n")
        env = {"PATH": self.bin + ":" + os.environ["PATH"], "STATE": self.state}
        env.update(env_extra or {})
        if not as_root:
            os.remove(os.path.join(self.bin, "id"))          # skutočné `id -u` (nie root)
        done = subprocess.run(["sh", SCRIPT], env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=20)
        lines = []
        if os.path.exists(self.log):
            with open(self.log) as f:
                lines = f.read().splitlines()
        return done, lines

    def test_creates_both_accounts_as_plain_users_with_private_home_and_trash(self):
        done, log = self.run_script()
        self.assertEqual(done.returncode, 0, done.stderr)
        useradds = [l for l in log if l.startswith("useradd")]
        self.assertEqual(len(useradds), 2)
        self.assertIn("--create-home", useradds[0])
        self.assertIn("arkay", useradds[0])
        self.assertIn("kenshi", useradds[1])
        for name in ("arkay", "kenshi"):
            self.assertIn("chmod 0700 /home/%s" % name, log)
            self.assertIn("install -d -m 0700 -o %s -g %s /home/%s/.local/share/Trash/files" % (name, name, name), log)
            self.assertIn("install -d -m 0700 -o %s -g %s /home/%s/.local/share/Trash/info" % (name, name, name), log)
        joined = " ".join(useradds)
        self.assertNotIn("wheel", joined)                    # bez práv správcu
        self.assertNotIn("-G", joined)
        self.assertNotIn("-p", joined.split())               # heslo sa nikdy nedáva na príkazový riadok

    def test_existing_account_is_left_alone_but_its_space_is_still_secured(self):
        done, log = self.run_script(existing=["arkay"])
        self.assertEqual(done.returncode, 0, done.stderr)
        useradds = [l for l in log if l.startswith("useradd")]
        self.assertEqual(len(useradds), 1)
        self.assertIn("kenshi", useradds[0])
        self.assertIn("už existuje", done.stdout)
        self.assertIn("chmod 0700 /home/arkay", log)

    def test_without_a_terminal_it_tells_how_to_set_the_password(self):
        done, log = self.run_script()
        self.assertIn("passwd arkay", done.stdout)
        self.assertIn("passwd kenshi", done.stdout)
        self.assertFalse([l for l in log if l.startswith("passwd")])

    def test_custom_list_with_a_full_name_containing_a_space(self):
        done, log = self.run_script(env_extra={"USERS": "anna:Anna Nováková,peter:Peter"})
        useradds = [l for l in log if l.startswith("useradd")]
        self.assertEqual([l.split()[-1] for l in useradds], ["anna", "peter"])   # „Nováková“ nie je samostatný účet
        self.assertIn("Anna Nováková", useradds[0])
        self.assertFalse([l for l in log if "Nováková" in l and l.startswith("useradd") and l.split()[-1] == "Nováková"])

    def test_refuses_to_run_without_root(self):
        done, log = self.run_script(as_root=False)
        if os.getuid() == 0:
            self.skipTest("testy bežia ako root")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("root", done.stderr)
        self.assertEqual(log, [])


if __name__ == "__main__":
    unittest.main()
