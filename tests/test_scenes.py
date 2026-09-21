import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import cairo  # noqa: E402

from latte_common import scenes  # noqa: E402


def frame(scene, t, width=168, height=84, canvas=(640, 194), clip=None):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(surface)
    if clip:
        cr.rectangle(*clip)
        cr.clip()
    scene.render(cr, canvas[0], canvas[1], t)
    surface.flush()
    return bytes(surface.get_data())


class ParseTest(unittest.TestCase):
    def test_solid_color(self):
        scene = scenes.parse("solid:#FF8000")
        self.assertIsInstance(scene, scenes.Solid)
        self.assertEqual(scene.rgb, (1.0, 128 / 255, 0.0))
        self.assertFalse(scene.animated)

    def test_matrix(self):
        self.assertIsInstance(scenes.parse("scene:matrix"), scenes.Matrix)
        self.assertEqual(scenes.parse("scene:matrix", speed=0.5).speed, 0.5)

    def test_unknown_or_broken_spec_is_none(self):
        for spec in ("", None, "matrix", "scene:nic", "solid:red", "solid:#12", "file:", "x:y:z"):
            self.assertIsNone(scenes.parse(spec), spec)


class MatrixTest(unittest.TestCase):
    def test_same_time_gives_same_picture(self):
        self.assertEqual(frame(scenes.Matrix(), 3.0), frame(scenes.Matrix(), 3.0))

    def test_picture_depends_only_on_time_not_on_earlier_frames(self):
        used = scenes.Matrix()
        for t in (0.5, 1.5, 9.0):
            frame(used, t)
        self.assertEqual(frame(used, 3.0), frame(scenes.Matrix(), 3.0))

    def test_picture_moves(self):
        scene = scenes.Matrix()
        self.assertNotEqual(frame(scene, 1.0), frame(scene, 4.0))

    def test_speed_changes_the_picture_not_the_look(self):
        self.assertNotEqual(frame(scenes.Matrix(1.0), 5.0), frame(scenes.Matrix(0.25), 5.0))

    def test_paints_only_inside_the_clip(self):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 168, 84)
        cr = cairo.Context(surface)
        cr.rectangle(0, 0, 50, 40)
        cr.clip()
        scenes.Matrix().render(cr, 640, 194, 3.0)
        surface.flush()
        data = surface.get_data()
        stride = surface.get_stride()

        def alpha(x, y):
            return data[y * stride + x * 4 + 3]

        self.assertEqual(alpha(10, 10), 255)             # v orezaní je podklad
        self.assertEqual(alpha(100, 60), 0)              # mimo orezania sa nekreslí nič

    def test_background_is_opaque_everywhere_in_view(self):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 168, 84)
        scenes.Matrix().render(cairo.Context(surface), 640, 194, 0.0)
        surface.flush()
        data = surface.get_data()
        self.assertTrue(all(data[i] == 255 for i in range(3, len(data), 4)))

    def test_still_time_is_a_real_picture(self):
        """Statický snímok pri vypnutom pohybe nesmie byť prázdny podklad."""
        scene = scenes.Matrix()
        plain = frame(scene, scenes.STILL_TIME)
        background = bytes(bytearray(int(c * 255 + 0.5) for c in reversed(scenes.Matrix.BACKGROUND)) + b"\xff")
        self.assertNotEqual(plain, background * (168 * 84))


class ParseMoreTest(unittest.TestCase):
    def test_new_scenes(self):
        self.assertIsInstance(scenes.parse("scene:gears"), scenes.Gears)
        self.assertIsInstance(scenes.parse("scene:glow"), scenes.Glow)
        self.assertTrue(scenes.parse("scene:gears", right=True).right)

    def test_plain_tile_is_a_known_source_without_a_scene(self):
        self.assertIsNone(scenes.parse(scenes.PLAIN))
        self.assertTrue(scenes.is_known(scenes.PLAIN))

    def test_known_and_unknown_sources(self):
        for spec in ("scene:matrix", "scene:gears", "scene:glow", "solid:#102030", "file:/x.gif", scenes.PLAIN):
            self.assertTrue(scenes.is_known(spec), spec)
        for spec in ("", None, "scene:nic", "solid:red", "file:x.gif", "matrix"):
            self.assertFalse(scenes.is_known(spec), repr(spec))

    def test_every_offered_choice_is_known_and_labelled(self):
        for spec, label in scenes.CHOICES:
            self.assertTrue(scenes.is_known(spec), spec)
            self.assertTrue(label)
        self.assertEqual(scenes.CHOICES[0][0], scenes.PLAIN)

    def test_custom_labels_for_settings(self):
        self.assertEqual(scenes.custom_label("file:/home/u/tapety/kava.gif"), "Súbor: kava.gif")
        self.assertEqual(scenes.custom_label("solid:#0b120c"), "Farba: #0B120C")
        self.assertIn("neznámy", scenes.custom_label("scene:nic"))
        self.assertIn("neznámy", scenes.custom_label(""))
        self.assertIn("neznámy", scenes.custom_label(None))

    def test_palette_from_theme_colours(self):
        palette = scenes.palette_from_colors({"accent": "#FF8000", "fg": "#000000"})
        self.assertEqual(palette.accent, (1.0, 128 / 255, 0.0))
        self.assertEqual(palette.fg, (0.0, 0.0, 0.0))
        self.assertEqual(scenes.palette_from_colors({"accent": "zle"}), scenes.DEFAULT_PALETTE)
        self.assertEqual(scenes.palette_from_colors({}), scenes.DEFAULT_PALETTE)

    def test_palette_reaches_the_scene(self):
        palette = scenes.Palette(accent=(0.1, 0.2, 0.3), fg=(0.9, 0.8, 0.7))
        self.assertEqual(scenes.parse("scene:gears", palette=palette).palette, palette)


class SourceListTest(unittest.TestCase):
    """Rozbaľovací zoznam zdrojov v Nastaveniach. Chyba z reálnej relácie: výber „Jedna farba“ zavesil Nastavenia
    (nekonečné zapisovanie a obnovovanie), lebo obsluha výberu nebola idempotentná."""

    def test_offered_values_have_no_custom_entry(self):
        for i, (spec, _label) in enumerate(scenes.CHOICES):
            specs, labels, index = scenes.source_list(spec)
            self.assertEqual((specs, index), ([s for s, _l in scenes.CHOICES], i))
            self.assertEqual(len(labels), len(scenes.CHOICES))

    def test_other_values_get_one_custom_entry_at_the_end(self):
        for value, label in (("file:/a/b/kava.gif", "Súbor: kava.gif"), ("solid:#102030", "Farba: #102030"),
                             ("scene:nic", "scene:nic (neznámy zdroj)")):
            specs, labels, index = scenes.source_list(value)
            self.assertEqual(len(specs), len(scenes.CHOICES) + 1)
            self.assertEqual((specs[index], labels[index], index), (value, label, len(specs) - 1))

    def test_labels_are_equal_for_equal_values_so_the_model_is_not_rebuilt(self):
        self.assertEqual(scenes.source_list("file:/a/x.gif")[1], scenes.source_list("file:/a/x.gif")[1])
        self.assertEqual(scenes.source_list("scene:matrix")[1], scenes.source_list("scene:glow")[1])

    def test_picking_the_current_value_writes_nothing(self):
        """Oznámenie o výbere, ktorý nastavil program, nesmie nič zapísať."""
        values = [spec for spec, _l in scenes.CHOICES] + ["file:/a/x.gif", "solid:#102030", "scene:nic", ""]
        for value in values:
            specs, _labels, index = scenes.source_list(value)
            self.assertIsNone(scenes.pick_source(specs, index, value), value)

    def test_picking_another_item_writes_it(self):
        specs, _labels, _index = scenes.source_list("scene:matrix")
        self.assertEqual(scenes.pick_source(specs, 0, "scene:matrix"), scenes.PLAIN)
        self.assertEqual(scenes.pick_source(specs, 2, "scene:matrix"), "scene:gears")

    def test_out_of_range_selection_writes_nothing(self):
        specs, _labels, _index = scenes.source_list("scene:matrix")
        for index in (-1, len(specs), 4294967295):                  # GTK_INVALID_LIST_POSITION je uint max
            self.assertIsNone(scenes.pick_source(specs, index, "scene:matrix"))

    def test_the_write_refresh_select_cycle_terminates(self):
        """Simulácia slučky: zápis → obnova zoznamu → doručené oznámenie → (zápis?). Musí sa zastaviť po jednom zápise."""
        stored, writes = "scene:matrix", 0
        specs, _labels, _index = scenes.source_list(stored)
        pending = [0]                                                # používateľ vybral položku 0
        for _ in range(50):                                          # GTK by to točilo donekonečna
            if not pending:
                break
            choice = scenes.pick_source(specs, pending.pop(), stored)
            if choice is None:
                continue
            stored, writes = choice, writes + 1
            specs, _labels, index = scenes.source_list(stored)       # obnova zoznamu
            pending.append(index)                                    # oznámenie o nastavenom výbere
        self.assertEqual(writes, 1)
        self.assertFalse(pending)


class GearsTest(unittest.TestCase):
    W, H = 820, 194

    def setUp(self):
        self.scene = scenes.Gears()
        self.gears = self.scene.gears(self.W, self.H)

    def test_layout_is_fixed(self):
        self.assertEqual(self.gears, scenes.Gears().gears(self.W, self.H))

    def test_there_are_enough_gears_spread_across_the_width(self):
        self.assertGreaterEqual(len(self.gears), 12)
        self.assertGreater(max(g.x for g in self.gears), self.W * 0.7)

    def test_meshing_gears_touch_at_their_pitch_circles(self):
        for g in self.gears[1:]:
            p = self.gears[g.parent]
            self.assertLess(g.parent, self.gears.index(g))
            self.assertAlmostEqual(math.hypot(g.x - p.x, g.y - p.y), g.r + p.r, places=6)

    def test_other_gears_never_overlap(self):
        for i, a in enumerate(self.gears):
            for j, b in enumerate(self.gears):
                if i < j and a.parent != j and b.parent != i:
                    self.assertGreaterEqual(math.hypot(a.x - b.x, a.y - b.y), a.r + b.r + 2 * self.scene.MODULE - 1e-6)

    def test_nothing_in_the_notch_under_the_arm(self):
        for g in self.gears:
            self.assertFalse(g.x > self.scene.DEAD_X and g.y > self.scene.DEAD_Y * self.H, g)

    def test_teeth_fit_into_gaps_at_every_moment(self):
        for t in (0.0, 1.7, 13.3, 250.0):
            angles = self.scene.angles(self.gears, t)
            for g in self.gears[1:]:
                p = self.gears[g.parent]
                u = (g.alpha - angles[g.parent]) * p.n            # fáza zuba rodiča v mieste dotyku
                v = (g.alpha + math.pi - angles[self.gears.index(g)]) * g.n
                self.assertAlmostEqual(math.cos(u + v - math.pi), 1.0, places=6, msg="t=%s" % t)

    def test_speeds_follow_the_tooth_ratio_and_direction(self):
        dt = 1e-3
        a, b = self.scene.angles(self.gears, 5.0), self.scene.angles(self.gears, 5.0 + dt)
        for i, g in enumerate(self.gears[1:], start=1):
            p = self.gears[g.parent]
            ratio = (b[i] - a[i]) / (b[g.parent] - a[g.parent])
            self.assertAlmostEqual(ratio, -p.n / g.n, places=6)

    def test_drive_gear_turns_calmly(self):
        angles = self.scene.angles(self.gears, 10.0)
        self.assertLess(abs(angles[0]) / 10.0, 0.5)              # menej než pol radiánu za sekundu

    def test_speed_setting_scales_the_rotation(self):
        slow = scenes.Gears(speed=0.5)
        self.assertAlmostEqual(slow.angles(slow.gears(self.W, self.H), 8.0)[0],
                               0.5 * self.scene.angles(self.gears, 8.0)[0])

    def test_right_corner_is_the_mirror_image(self):
        left = frame(scenes.Gears(), 4.0, self.W, self.H, (self.W, self.H))
        right = frame(scenes.Gears(right=True), 4.0, self.W, self.H, (self.W, self.H))
        total, worst, count = 0, 0, 0
        for y in range(self.H):
            row_l = left[y * self.W * 4:(y + 1) * self.W * 4]
            row_r = right[y * self.W * 4:(y + 1) * self.W * 4]
            mirrored = b"".join(row_l[x * 4:x * 4 + 4] for x in range(self.W - 1, -1, -1))
            for a, b in zip(mirrored, row_r):
                total += abs(a - b)
                worst = max(worst, abs(a - b))
                count += 1
        # hrany kolies sa vyhladzujú v zrkadle trochu inak (zaokrúhlenie), inak je obraz rovnaký
        self.assertLess(total / count, 0.5)
        self.assertLessEqual(worst, 40)

    def test_same_time_same_picture_and_it_moves(self):
        self.assertEqual(frame(scenes.Gears(), 2.0), frame(scenes.Gears(), 2.0))
        self.assertNotEqual(frame(scenes.Gears(), 2.0), frame(scenes.Gears(), 9.0))

    def test_paints_only_inside_the_clip(self):
        data = frame(scenes.Gears(), 3.0, clip=(0, 0, 50, 40))
        self.assertEqual(data[(60 * 168 + 100) * 4 + 3], 0)


class SceneSideEffectsTest(unittest.TestCase):
    def test_no_scene_leaves_the_context_transformed_or_clipped_differently(self):
        """Kto kreslí po scéne (tmavý prechod), potrebuje nezmenenú transformáciu a rovnaké orezanie."""
        for spec, right in (("scene:matrix", False), ("scene:gears", False), ("scene:gears", True),
                            ("scene:glow", False), ("solid:#102030", False)):
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 820, 194)
            cr = cairo.Context(surface)
            cr.rectangle(10, 20, 300, 100)
            cr.clip()
            before = (cr.get_matrix(), cr.clip_extents())
            scenes.parse(spec, right=right).render(cr, 820, 194, 3.0)
            self.assertEqual((cr.get_matrix(), cr.clip_extents()), before, spec)


class GlowTest(unittest.TestCase):
    def test_deterministic_and_moving(self):
        self.assertEqual(frame(scenes.Glow(), 3.0), frame(scenes.Glow(), 3.0))
        self.assertNotEqual(frame(scenes.Glow(), 3.0), frame(scenes.Glow(), 30.0))

    def test_blobs_stay_on_the_canvas(self):
        glow = scenes.Glow()
        for t in (0, 10, 100, 1000):
            for blob in glow.blobs:
                x, y = glow.center(blob, 820, 194, t)
                self.assertTrue(0 <= x <= 820 and 0 <= y <= 194)

    def test_paints_only_inside_the_clip(self):
        data = frame(scenes.Glow(), 3.0, clip=(0, 0, 50, 40))
        self.assertEqual(data[(60 * 168 + 100) * 4 + 3], 0)

    def test_calm(self):
        """Škvrna sa za sekundu posunie o pár pixelov, nie o desiatky."""
        glow = scenes.Glow()
        for blob in glow.blobs:
            a, b = glow.center(blob, 820, 194, 10.0), glow.center(blob, 820, 194, 11.0)
            self.assertLess(math.hypot(a[0] - b[0], a[1] - b[1]), 45)


class DimOverlayTest(unittest.TestCase):
    W, H, BAR, FOOT = 820, 194, 84, 168

    def overlay(self, dim, right=False):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.W, self.H)
        scenes.dim_overlay(cairo.Context(surface), self.W, self.H, self.BAR, self.FOOT, dim, right)
        surface.flush()
        data, stride = surface.get_data(), surface.get_stride()
        return lambda x, y: data[y * stride + x * 4 + 3]

    def test_no_dim_draws_nothing(self):
        alpha = self.overlay(0)
        self.assertEqual(sum(alpha(x, y) for x in range(0, self.W, 20) for y in range(0, self.H, 10)), 0)

    def test_notch_under_the_arm_stays_clear(self):
        alpha = self.overlay(0.6)
        self.assertEqual(alpha(400, 150), 0)

    def test_trunk_is_lighter_near_the_foot_and_darker_under_the_text(self):
        alpha = self.overlay(0.6)
        self.assertLess(alpha(20, 50), alpha(500, 50))
        self.assertGreater(alpha(500, 50), 150)

    def test_right_corner_is_the_mirror(self):
        left, right = self.overlay(0.6), self.overlay(0.6, right=True)
        for x, y in ((20, 50), (500, 50), (100, 150), (300, 10)):
            self.assertEqual(left(x, y), right(self.W - 1 - x, y))

    def test_stronger_dim_is_darker(self):
        self.assertLess(self.overlay(0.3)(500, 50), self.overlay(0.8)(500, 50))

    def test_foot_is_darker_at_the_bottom_where_the_label_is(self):
        alpha = self.overlay(0.6)
        self.assertLess(alpha(80, 120), alpha(80, 190))


if __name__ == "__main__":
    unittest.main()
