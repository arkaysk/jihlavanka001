import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_shell import reveal  # noqa: E402


class EasingTest(unittest.TestCase):
    def test_endpoints_and_clamping(self):
        for fn in (reveal.ease_out, reveal.smooth):
            self.assertEqual(fn(0), 0)
            self.assertEqual(fn(1), 1)
            self.assertEqual(fn(-3), 0)
            self.assertEqual(fn(7), 1)

    def test_monotonic(self):
        for fn in (reveal.ease_out, reveal.smooth):
            values = [fn(i / 50) for i in range(51)]
            self.assertEqual(values, sorted(values))


class PhasesTest(unittest.TestCase):
    def test_closed_and_open(self):
        self.assertEqual(reveal.phases(0.0), (0.0, 0.0))
        self.assertEqual(reveal.phases(1.0), (1.0, 1.0))

    def test_panel_waits_for_the_trunk(self):
        """Panel sa začne objavovať, až keď je kmeň z veľkej časti odhalený."""
        arm, panel = reveal.phases(reveal.PANEL_FROM)
        self.assertEqual(panel, 0.0)
        self.assertGreater(arm, 0.9)

    def test_trunk_is_complete_before_the_end(self):
        self.assertEqual(reveal.phases(reveal.ARM_SHARE)[0], 1.0)

    def test_both_grow_monotonically(self):
        steps = [reveal.phases(i / 100) for i in range(101)]
        self.assertEqual([s[0] for s in steps], sorted(s[0] for s in steps))
        self.assertEqual([s[1] for s in steps], sorted(s[1] for s in steps))


class RevealRectTest(unittest.TestCase):
    def test_closed_is_a_flat_strip_the_width_of_the_foot_on_the_bottom_edge(self):
        self.assertEqual(reveal.reveal_rect(0, 820, 110, 168), (0.0, 110, 168, 0))

    def test_open_is_everything(self):
        self.assertEqual(reveal.reveal_rect(1, 820, 110, 168), (0.0, 0, 820, 110))

    def test_grows_from_the_bottom_edge_next_to_the_foot(self):
        x, y, w, h = reveal.reveal_rect(0.5, 820, 110, 168)
        self.assertEqual((x, w, h), (0.0, 494.0, 55.0))
        self.assertEqual(y + h, 110)                       # spodná hrana je stále pri päte

    def test_right_side_is_anchored_to_the_right_edge(self):
        x, y, w, h = reveal.reveal_rect(0.5, 820, 110, 168, right=True)
        self.assertEqual(x + w, 820)
        self.assertEqual(w, 494.0)


if __name__ == "__main__":
    unittest.main()
