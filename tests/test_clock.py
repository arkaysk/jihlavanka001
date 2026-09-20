import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import clock, prefs  # noqa: E402


class ClockTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = prefs.CONFIG_DIR
        prefs.CONFIG_DIR = self._tmp.name
        self._tz = os.environ.get("TZ")
        os.environ["TZ"] = "Europe/Bratislava"
        import time
        time.tzset()

    def tearDown(self):
        prefs.CONFIG_DIR = self._old
        if self._tz is None:
            del os.environ["TZ"]
        else:
            os.environ["TZ"] = self._tz
        import time
        time.tzset()
        self._tmp.cleanup()

    def test_defaults_until_the_user_chooses(self):
        self.assertEqual(clock.load_zones(), clock.DEFAULT_ZONES)

    def test_add_is_case_insensitive_and_persists(self):
        self.assertIsNone(clock.add_zone("europe/paris"))
        self.assertIn("Europe/Paris", clock.load_zones())

    def test_add_rejects_unknown_and_duplicate_zones(self):
        self.assertIn("neexistuje", clock.add_zone("Mars/Olympus"))
        self.assertIn("už v zozname", clock.add_zone("Asia/Tokyo"))
        self.assertIn("Napíš", clock.add_zone("  "))

    def test_spaces_stand_for_underscores(self):
        self.assertIsNone(clock.add_zone("America/Los Angeles"))
        self.assertIn("America/Los_Angeles", clock.load_zones())

    def test_remove_can_leave_the_list_empty(self):
        for zone in list(clock.load_zones()):
            clock.remove_zone(zone)
        self.assertEqual(clock.load_zones(), [])

    def test_broken_zone_in_the_file_is_skipped(self):
        prefs.update("clock", zones="Asia/Tokyo,Zle/Miesto,Asia/Tokyo")
        self.assertEqual(clock.load_zones(), ["Asia/Tokyo"])

    def test_row_shows_time_day_and_difference(self):
        now = datetime(2026, 9, 19, 22, 30, tzinfo=timezone.utc)      # v Bratislave 00:30 (20.)
        self.assertEqual(clock.zone_row(now, "Asia/Tokyo"), ("Tokyo", "07:30", "dnes", "+7 h"))
        self.assertEqual(clock.zone_row(now, "America/New_York"), ("New York", "18:30", "včera", "-6 h"))
        self.assertEqual(clock.zone_row(now, "Europe/Bratislava")[3], "rovnaký čas")

    def test_half_hour_offsets(self):
        now = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(clock.zone_row(now, "Asia/Kolkata")[3], "+3:30 h")

    def test_ago(self):
        self.assertEqual([clock.ago(1000, t) for t in (990, 700, 100, 1000 - 90000)],
                         ["teraz", "pred 5 min", "pred 15 min", "pred 1 d"])
        self.assertEqual(clock.ago(10000, 10000 - 7300), "pred 2 h")

    def test_city_name(self):
        self.assertEqual(clock.city("America/Argentina/Buenos_Aires"), "Buenos Aires")


if __name__ == "__main__":
    unittest.main()
