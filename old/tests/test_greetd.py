import os
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from fake_greetd import FakeGreetd  # noqa: E402
from latte_greeter import greetd  # noqa: E402


class LoginFlowTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, "greetd.sock")
        self.server = FakeGreetd(self.path)
        self.flow = greetd.LoginFlow(greetd.Client(self.path))

    def tearDown(self):
        self.flow.client.close()
        self.server.close()
        self._tmp.cleanup()

    def types(self):
        return [m["type"] for m in self.server.log]

    def test_password_account_asks_then_accepts(self):
        outcome = self.flow.begin("test")
        self.assertEqual(outcome.kind, "prompt")
        self.assertTrue(outcome.secret)
        self.assertEqual(self.flow.answer("kava").kind, "success")
        self.assertEqual(self.flow.start(["latteos-session"]).kind, "success")
        self.assertEqual(self.server.log[-1]["cmd"], ["latteos-session"])

    def test_wrong_password_is_auth_error_and_session_is_cancelled(self):
        self.flow.begin("test")
        outcome = self.flow.answer("zle")
        self.assertEqual(outcome.kind, "error")
        self.assertTrue(outcome.auth_error)
        # po chybe sa dá začať odznova
        self.assertEqual(self.flow.begin("test").kind, "prompt")
        self.assertEqual(self.flow.answer("kava").kind, "success")

    def test_account_without_password_logs_in_at_once(self):
        # greeter to nezisťuje vopred: create_session rovno vráti success
        self.assertEqual(self.flow.begin("guest").kind, "success")
        self.assertNotIn("post_auth_message_response", self.types())

    def test_unknown_user_looks_like_wrong_password(self):
        self.assertEqual(self.flow.begin("nikto").kind, "prompt")
        outcome = self.flow.answer("hocico")
        self.assertTrue(outcome.auth_error)

    def test_switching_user_cancels_previous_session(self):
        self.flow.begin("test")
        self.flow.begin("guest")
        self.assertIn("cancel_session", self.types())

    def test_cancel_only_when_a_session_is_open(self):
        self.flow.cancel()
        self.assertEqual(self.types(), [])
        self.flow.begin("test")
        self.flow.cancel()
        self.assertEqual(self.types()[-1], "cancel_session")

    def test_start_without_authentication_is_an_error(self):
        self.flow.begin("test")
        outcome = self.flow.start(["latteos-session"])
        self.assertEqual(outcome.kind, "error")


class ClientTest(unittest.TestCase):
    def test_missing_socket_variable(self):
        old = os.environ.pop("GREETD_SOCK", None)
        try:
            with self.assertRaises(greetd.GreetdError):
                greetd.Client().request({"type": "cancel_session"})
        finally:
            if old is not None:
                os.environ["GREETD_SOCK"] = old

    def test_dead_socket(self):
        with self.assertRaises(greetd.GreetdError):
            greetd.Client("/nonexistent/greetd.sock").request({"type": "cancel_session"})


if __name__ == "__main__":
    unittest.main()
