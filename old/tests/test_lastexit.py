import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import lastexit  # noqa: E402

CRASH = "TIME=%d\nKIND=crash\nSTATUS=139\nSIGNAL=SEGV\nUPTIME=42\nCOMPONENT=labwc\n" % int(time.time())


class ParseTest(unittest.TestCase):
    def test_crash_record(self):
        rec = lastexit.parse(CRASH)
        self.assertEqual((rec.kind, rec.status, rec.signal, rec.uptime), ("crash", 139, "SEGV", 42))
        self.assertTrue(rec.is_problem)
        self.assertFalse(rec.quick)

    def test_unknown_kind_or_empty_is_rejected(self):
        self.assertIsNone(lastexit.parse(""))
        self.assertIsNone(lastexit.parse("KIND=rm -rf\nSTATUS=1"))

    def test_fields_are_validated_because_the_login_screen_shows_them(self):
        rec = lastexit.parse("KIND=crash\nSIGNAL=<b>x</b>\nCOMPONENT=../../etc\nSTATUS=abc\nUPTIME=-5\n")
        self.assertEqual(rec.signal, "")
        self.assertEqual(rec.component, "labwc")
        self.assertEqual((rec.status, rec.uptime), (0, 0))

    def test_normal_record_is_not_a_problem(self):
        self.assertFalse(lastexit.parse("KIND=normal\nSTATUS=0").is_problem)


class ReadTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, text):
        with open(os.path.join(self.dir, name), "w") as f:
            f.write(text)

    def test_reads_per_user(self):
        self.write("arkay", CRASH)
        self.assertEqual(lastexit.read("arkay", self.dir).kind, "crash")
        self.assertIsNone(lastexit.read("iny", self.dir))

    def test_normal_end_shows_nothing(self):
        self.write("arkay", "KIND=normal\nSTATUS=0\n")
        self.assertIsNone(lastexit.read("arkay", self.dir))

    def test_username_cannot_escape_directory(self):
        self.write("arkay", CRASH)
        self.assertIsNone(lastexit.read("../" + os.path.basename(self.dir) + "/arkay", self.dir))
        self.assertIsNone(lastexit.read("", self.dir))


class DescribeTest(unittest.TestCase):
    def test_crash_text(self):
        title, detail = lastexit.describe(lastexit.parse(CRASH))
        self.assertEqual(title, "Posledná relácia spadla")
        self.assertIn("SEGV", detail)
        self.assertIn("42 s", detail)

    def test_quick_failure_is_reported_as_not_started(self):
        rec = lastexit.parse("KIND=error\nSTATUS=1\nUPTIME=1\n")
        self.assertTrue(rec.quick)
        self.assertEqual(lastexit.describe(rec)[0], "Relácia sa nespustila")

    def test_missing_labwc(self):
        title, detail = lastexit.describe(lastexit.parse("KIND=missing\nSTATUS=127\n"))
        self.assertIn("nepodarilo spustiť", title)
        self.assertIn("127", detail)


if __name__ == "__main__":
    unittest.main()
