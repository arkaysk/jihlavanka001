import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import termrun, textmark  # noqa: E402


class TermrunTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = os.path.realpath(self._tmp.name)
        self.cwd_file = os.path.join(self.dir, "cwd")

    def tearDown(self):
        self._tmp.cleanup()

    def saved_cwd(self):
        with open(self.cwd_file) as f:
            return f.read().strip()

    def run_command(self, command, cwd=None):
        proc = subprocess.run(termrun.argv(command, self.cwd_file), cwd=cwd or self.dir,
                              capture_output=True, text=True, env=termrun.environment(), timeout=10,
                              stdin=subprocess.DEVNULL)
        return proc

    def test_runs_in_the_given_directory_and_reports_it(self):
        proc = self.run_command("pwd")
        self.assertEqual(proc.stdout.strip(), self.dir)
        self.assertEqual(self.saved_cwd(), self.dir)

    def test_cd_is_remembered_even_inside_a_chain(self):
        os.makedirs(os.path.join(self.dir, "pod", "priecinok"))
        self.run_command("cd pod && cd priecinok")
        self.assertEqual(self.saved_cwd(), os.path.join(self.dir, "pod", "priecinok"))

    def test_exit_code_is_kept(self):
        self.assertEqual(self.run_command("false").returncode, 1)
        self.assertEqual(self.run_command("echo ok").returncode, 0)

    def test_stdin_is_closed_so_prompts_cannot_hang(self):
        self.assertEqual(self.run_command("cat").returncode, 0)

    def test_environment_asks_for_plain_output(self):
        env = termrun.environment({"PATH": "/bin"})
        self.assertEqual((env["TERM"], env["NO_COLOR"], env["PAGER"]), ("dumb", "1", "cat"))

    def test_layer_shell_preload_of_the_bar_is_not_inherited(self):
        env = termrun.environment({"LD_PRELOAD": "/usr/lib64/libgtk4-layer-shell.so.1"})
        self.assertNotIn("LD_PRELOAD", env)
        env = termrun.environment({"LD_PRELOAD": "/x/libgtk4-layer-shell.so /x/jine.so"})
        self.assertEqual(env["LD_PRELOAD"], "/x/jine.so")

    def test_command_is_its_own_process_group_so_it_can_be_interrupted(self):
        proc = self.run_command('ps -o pid=,pgid= -p $$')
        pid, pgid = proc.stdout.split()
        self.assertEqual(pid, pgid)

    def test_strip_ansi(self):
        self.assertEqual(termrun.strip_ansi("\x1b[1;31mchyba\x1b[0m\r\n\x1b]0;titul\x07ok"),
                         "chyba\nok")

    def test_needs_terminal(self):
        for command in ("vim súbor", "htop", "sudo dnf update", "ssh host", "LANG=C less x",
                        "python3", "/usr/bin/nano a"):
            self.assertTrue(termrun.needs_terminal(command), command)
        for command in ("ls -la", "python3 skript.py", "echo vim", "git log", "", "cd /tmp"):
            self.assertFalse(termrun.needs_terminal(command), command)

    def test_terminal_argv_needs_foot(self):
        with mock.patch("shutil.which", return_value=None):
            self.assertIsNone(termrun.terminal_argv("vim", "/tmp"))
        with mock.patch("shutil.which", return_value="/usr/bin/foot"):
            argv = termrun.terminal_argv("vim x", "/tmp")
        self.assertEqual(argv[:3], ["foot", "--working-directory", "/tmp"])
        self.assertEqual(argv[-1], "vim x")

    def test_pretty_cwd(self):
        self.assertEqual(termrun.pretty_cwd("/home/u", "/home/u"), "~")
        self.assertEqual(termrun.pretty_cwd("/home/u/dev", "/home/u"), "~/dev")
        self.assertEqual(termrun.pretty_cwd("/home/ux", "/home/u"), "/home/ux")


class TextmarkTest(unittest.TestCase):
    def test_bold_code_heading_and_bullets(self):
        out = textmark.to_pango("# Titul\n- **tučné** a `kód`\n* druhá")
        self.assertEqual(out, "<b>Titul</b>\n• <b>tučné</b> a <tt>kód</tt>\n• druhá")

    def test_code_fence_is_monospace_and_escaped(self):
        out = textmark.to_pango("```python\nif a < b: **x**\n```\nkoniec")
        self.assertEqual(out, "<tt>if a &lt; b: **x**</tt>\nkoniec")

    def test_unfinished_markup_stays_literal(self):
        self.assertEqual(textmark.to_pango("a `neuzavrete"), "a `neuzavrete")
        self.assertEqual(textmark.to_pango("a **neuzavrete"), "a **neuzavrete")

    def test_text_is_escaped(self):
        self.assertEqual(textmark.to_pango("<b>&"), "&lt;b&gt;&amp;")

    def test_result_is_valid_pango_markup(self):
        try:
            import gi
            gi.require_version("Pango", "1.0")
            from gi.repository import Pango
        except (ImportError, ValueError):
            self.skipTest("Pango nie je dostupné")
        text = "# H\n**a `b` c**\n```\n<x> & y\n```\n- `k` **t**\nzvyšok `otvorený"
        Pango.parse_markup(textmark.to_pango(text), -1, "\0")


if __name__ == "__main__":
    unittest.main()
