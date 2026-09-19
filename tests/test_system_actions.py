import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_shell import system  # noqa: E402


class SystemActionsTest(unittest.TestCase):
    def test_logout_runs_the_helper_as_a_separate_user_unit(self):
        # lišta skončí spolu s reláciou, preto sa poradie krokov necháva pomocníkovi
        argv = system.command("logout")
        self.assertEqual(argv[:3], ["systemd-run", "--user", "--collect"])
        self.assertIn("--unit=latteos-logout", argv)
        self.assertEqual(os.path.basename(argv[-1]), "latteos-logout")
        self.assertNotIn("--console", argv)

    def test_helper_gets_the_values_the_manager_forgets_after_logout(self):
        argv = system.command("logout")
        self.assertIn("--setenv=LABWC_PID", argv)
        self.assertIn("--setenv=XDG_SESSION_ID", argv)

    def test_console_adds_the_flag_when_greetd_runs(self):
        argv = system.command("console", greetd=True)
        self.assertEqual(argv[-1], "--console")

    def test_console_without_greetd_is_just_a_logout(self):
        # relácia spustená ručne z konzoly: konzola tam už je
        self.assertEqual(system.command("console", greetd=False), system.command("logout"))

    def test_unknown_action(self):
        with self.assertRaises(ValueError):
            system.command("reboot")

    def test_needs_labwc_pid(self):
        argv = system.command("logout")
        self.assertIn("LABWC_PID", system.unavailable_reason(argv, environ={}))
        self.assertIsNone(system.unavailable_reason(argv, environ={"LABWC_PID": "123"}))

    def test_console_needs_the_polkit_rule_installed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            rule = os.path.join(d, "51-latteos-dev.rules")
            self.assertFalse(system.console_permitted(rule))
            open(rule, "w").close()
            self.assertTrue(system.console_permitted(rule))

    def test_helper_exists_and_is_executable(self):
        self.assertTrue(os.access(system.helper_path(), os.X_OK), system.helper_path())

    def test_every_action_has_a_command(self):
        for action in system.ACTIONS:
            self.assertTrue(system.command(action.id, greetd=True))


if __name__ == "__main__":
    unittest.main()
