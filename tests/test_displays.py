import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import displays, outputs  # noqa: E402


def head(name="HDMI-A-1", make="LG", model="27GL850", serial="123", modes=None, current=None, scale=1.0,
         transform=0, width_mm=597, height_mm=336, enabled=True, hid=10):
    """Head s režimami: modes = [(w, h, mHz, preferred)], current = index v modes."""
    h = outputs.Head(hid, name=name, make=make, model=model, serial=serial, width_mm=width_mm, height_mm=height_mm,
                     enabled=enabled, scale=scale, transform=transform)
    for i, (w, hh, r, pref) in enumerate(modes or []):
        h.modes[100 + i] = outputs.Mode(100 + i, w, hh, r, pref)
    if current is not None:
        h.current_mode = 100 + current
    return h


MODES = [(2560, 1440, 143912, True), (2560, 1440, 59951, False), (1920, 1080, 60000, False),
         (1920, 1080, 59940, False), (1280, 720, 60000, False)]


class IdentityTest(unittest.TestCase):
    def test_identity_is_the_monitor_not_the_port(self):
        a = head(name="HDMI-A-1")
        b = head(name="DP-2")
        self.assertEqual(list(displays.identify([a])), ["lg-27gl850-123"])
        self.assertEqual(list(displays.identify([b])), ["lg-27gl850-123"])       # iný port, ten istý monitor

    def test_two_identical_monitors_are_told_apart_by_connector(self):
        ids = displays.identify([head(name="DP-1", hid=1), head(name="DP-2", hid=2)])
        self.assertEqual(sorted(ids), ["lg-27gl850-123-dp-1", "lg-27gl850-123-dp-2"])

    def test_monitor_without_edid_falls_back_to_connector(self):
        self.assertEqual(list(displays.identify([head(name="Virtual-1", make="", model="", serial="")])), ["virtual-1"])

    def test_title(self):
        self.assertEqual(displays.title(head()), "LG 27GL850")
        self.assertEqual(displays.title(head(make="", model="", serial="", name="eDP-1")), "eDP-1")

    def test_diagonal(self):
        self.assertAlmostEqual(displays.diagonal_inches(head()), 27.0, delta=0.1)
        self.assertIsNone(displays.diagonal_inches(head(width_mm=0, height_mm=0)))


class OfferTest(unittest.TestCase):
    def setUp(self):
        self.head = head(modes=MODES, current=0)

    def test_resolutions_largest_first_without_duplicates(self):
        self.assertEqual(displays.resolutions(self.head), [(2560, 1440), (1920, 1080), (1280, 720)])

    def test_recommended_is_what_the_monitor_prefers(self):
        self.assertEqual(displays.recommended_resolution(self.head), (2560, 1440))
        self.assertEqual(displays.recommended_rate(self.head, 2560, 1440), 143912)
        # bez preferovaného režimu: najväčšie rozlíšenie a najvyššia frekvencia
        plain = head(modes=[(1024, 768, 60000, False), (800, 600, 75000, False), (800, 600, 60000, False)], current=0)
        self.assertEqual(displays.recommended_resolution(plain), (1024, 768))
        self.assertEqual(displays.recommended_rate(plain, 800, 600), 75000)

    def test_rates_highest_first(self):
        self.assertEqual(displays.rates(self.head, 1920, 1080), [60000, 59940])

    def test_unknown_rate_is_only_offered_when_nothing_else_is(self):
        self.assertEqual(displays.rates(head(modes=[(1280, 720, 0, False)]), 1280, 720), [0])
        self.assertEqual(displays.rates(head(modes=[(1280, 720, 0, False), (1280, 720, 60000, False)]), 1280, 720), [60000])

    def test_changing_resolution_keeps_the_rate_when_possible(self):
        self.assertEqual(displays.pick_rate(self.head, 1920, 1080, 59940), 59940)
        self.assertEqual(displays.pick_rate(self.head, 1920, 1080, 59950), 59940)        # v tolerancii
        self.assertEqual(displays.pick_rate(self.head, 1280, 720, 143912), 60000)        # nemá ju: odporúčaná
        self.assertEqual(displays.pick_rate(self.head, 1920, 1080), 60000)

    def test_recommended_scale_follows_density(self):
        self.assertEqual(displays.recommended_scale(self.head), 1.0)                     # 27″ 1440p ≈ 109 dpi
        dense = head(modes=[(3840, 2160, 60000, True)], current=0, width_mm=340, height_mm=190)   # 15″ 4K ≈ 285 dpi
        self.assertEqual(displays.recommended_scale(dense), 2.0)
        self.assertEqual(displays.recommended_scale(head(modes=MODES, current=0, width_mm=0, height_mm=0)), 1.0)

    def test_formatting(self):
        self.assertEqual(displays.format_resolution(2560, 1440), "2560 × 1440")
        self.assertEqual([displays.format_rate(r) for r in (60000, 59940, 143912, 0)],
                         ["60 Hz", "59,94 Hz", "143,91 Hz", "neznáma"])
        self.assertEqual(displays.format_scale(1.25), "125 %")
        self.assertEqual(displays.summary(self.head), "2560 × 1440 · 143,91 Hz · 100 %")
        self.assertEqual(displays.summary(head(modes=MODES, current=0, enabled=False)), "vypnutý")


class ChangeTest(unittest.TestCase):
    def setUp(self):
        self.head = head(modes=MODES, current=0)

    def test_no_change_means_empty(self):
        self.assertEqual(displays.change_for(self.head, *displays.current_state(self.head)), {})

    def test_only_what_differs_is_sent(self):
        self.assertEqual(displays.change_for(self.head, 2560, 1440, 143912, 1.5, "normal"), {"scale": 1.5})
        self.assertEqual(displays.change_for(self.head, 1920, 1080, 60000, 1.0, "90"),
                         {"mode": (1920, 1080, 60000), "transform": "90"})


class SavedTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, "cfg", "displays.toml")

    def tearDown(self):
        self._tmp.cleanup()

    def test_missing_file_is_empty_not_an_error(self):
        self.assertEqual(displays.load_saved(self.path), ({}, []))

    def test_round_trip_keeps_other_monitors(self):
        displays.save_monitor("lg-27gl850-123", 1920, 1080, 60000, 1.25, "90", self.path)
        displays.save_monitor("virtual-1", 1280, 720, 0, 1.0, "normal", self.path)
        saved, problems = displays.load_saved(self.path)
        self.assertEqual(problems, [])
        self.assertEqual(saved["lg-27gl850-123"], {"width": 1920, "height": 1080, "refresh": 60000,
                                                   "scale": 1.25, "transform": "90"})
        self.assertEqual(len(saved), 2)
        displays.forget_monitor("virtual-1", self.path)
        self.assertEqual(list(displays.load_saved(self.path)[0]), ["lg-27gl850-123"])

    def test_invalid_values_are_refused_on_save(self):
        for scale, transform in [(0.1, "normal"), (9, "normal"), (1.0, "sideways")]:
            with self.assertRaises(ValueError):
                displays.save_monitor("x", 800, 600, 60000, scale, transform, self.path)
        self.assertFalse(os.path.exists(self.path))

    def test_broken_file_is_reported_and_never_raises(self):
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, "w") as f:
            f.write("[monitor.a\nwidth = ")
        saved, problems = displays.load_saved(self.path)
        self.assertEqual(saved, {})
        self.assertEqual(len(problems), 1)

    def test_one_bad_entry_does_not_hide_the_good_ones(self):
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, "w") as f:
            f.write('[monitor.bad]\nwidth = "x"\nheight = 1\nrefresh = 0\n[monitor.good]\nwidth = 800\nheight = 600\n'
                    'refresh = 60000\nscale = 1.5\ntransform = "180"\n')
        saved, problems = displays.load_saved(self.path)
        self.assertEqual(list(saved), ["good"])
        self.assertIn("bad", problems[0])

    def test_plan_applies_only_differences_to_connected_monitors(self):
        h = head(modes=MODES, current=0)
        saved = {"lg-27gl850-123": {"width": 1920, "height": 1080, "refresh": 60000, "scale": 1.5, "transform": "normal"},
                 "iny-monitor": {"width": 800, "height": 600, "refresh": 60000, "scale": 1.0, "transform": "normal"}}
        changes, notes = displays.plan_saved([h], saved)
        self.assertEqual(changes, {"HDMI-A-1": {"mode": (1920, 1080, 60000), "scale": 1.5}})
        self.assertEqual(notes, [])
        same = {"lg-27gl850-123": dict(zip(("width", "height", "refresh", "scale", "transform"),
                                           displays.current_state(h)))}
        self.assertEqual(displays.plan_saved([h], same), ({}, []))

    def test_saved_mode_the_monitor_no_longer_has_is_reported_and_skipped(self):
        h = head(modes=MODES, current=0)
        saved = {"lg-27gl850-123": {"width": 3840, "height": 2160, "refresh": 30000, "scale": 1.5, "transform": "normal"}}
        changes, notes = displays.plan_saved([h], saved)
        self.assertEqual(changes, {"HDMI-A-1": {"scale": 1.5}})       # režim sa nemení, mierka áno
        self.assertEqual(len(notes), 1)
        self.assertIn("3840", notes[0])


if __name__ == "__main__":
    unittest.main()
