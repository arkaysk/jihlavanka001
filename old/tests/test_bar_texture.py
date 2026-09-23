import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import cairo  # noqa: E402

from latte_common import scenes  # noqa: E402
from latte_shell import bar_texture  # noqa: E402
from latte_shell import geometry  # noqa: E402
from latte_shell.geometry import TEXTURE_WIDTH  # noqa: E402

BAR_HEIGHT = geometry.DEFAULT_BAR_HEIGHT
CORNER_WIDTH = 2 * BAR_HEIGHT
TEXTURE_HEIGHT = BAR_HEIGHT + geometry.ARM_HEIGHT


class FakeSettings:
    """Náhrada Gtk.Settings: bez displeja Gtk.Settings.get_default() vráti None a testy nesmú závisieť od toho,
    či sa im podarí pripojiť k displeju živej relácie."""

    def __init__(self):
        self.values = {"gtk-enable-animations": True}

    def get_property(self, name):
        return self.values[name]

    def set_property(self, name, value):
        self.values[name] = value


class FakeView:
    def __init__(self, rect):
        self.rect = rect
        self.awake = False
        self.draws = 0

    def queue_draw(self):
        self.draws += 1


def alpha_at(texture, x, y_up):
    _px, py, _pw, _ph = texture.pixel_rect((x, y_up, 1, 1))
    texture.surface.flush()
    return texture.surface.get_data()[py * texture.surface.get_stride() + x * 4 + 3]


class BarTextureTest(unittest.TestCase):
    def setUp(self):
        self.texture = bar_texture.BarTexture(scenes.Matrix())
        if self.texture.settings is None:
            self.texture.settings = FakeSettings()
        self.animations = self.texture.settings.get_property("gtk-enable-animations")

    def tearDown(self):
        geometry.set_bar_height(geometry.DEFAULT_BAR_HEIGHT)
        for view in list(self.texture.views):
            self.texture.remove_view(view)
        self.texture.settings.set_property("gtk-enable-animations", self.animations)

    def test_canvas_origin_is_the_screen_corner_and_y_goes_up(self):
        self.assertEqual(self.texture.pixel_rect((0, 0, CORNER_WIDTH, BAR_HEIGHT)),
                         (0, TEXTURE_HEIGHT - BAR_HEIGHT, CORNER_WIDTH, BAR_HEIGHT))

    def test_corner_rects(self):
        self.assertEqual(bar_texture.corner_rect(False), (0, 0, CORNER_WIDTH, BAR_HEIGHT))
        self.assertEqual(bar_texture.corner_rect(True), (TEXTURE_WIDTH - CORNER_WIDTH, 0, CORNER_WIDTH, BAR_HEIGHT))

    def test_bar_height_change_resizes_the_canvas_and_moves_the_rects(self):
        geometry.set_bar_height(60)
        self.texture.set_bar_height()
        self.assertEqual((self.texture.surface.get_width(), self.texture.surface.get_height()),
                         (TEXTURE_WIDTH, 60 + geometry.ARM_HEIGHT))
        self.assertEqual(bar_texture.corner_rect(False), (0, 0, 120, 60))
        self.assertEqual(bar_texture.trunk_rect(), (0, 60, geometry.POPUP_WIDTH, geometry.ARM_HEIGHT))
        self.assertEqual(self.texture.pixel_rect(bar_texture.corner_rect(False)), (0, geometry.ARM_HEIGHT, 120, 60))

    def test_a_shown_view_is_redrawn_after_a_height_change(self):
        view = FakeView(bar_texture.corner_rect(False))
        self.texture.add_view(view)
        before = view.draws
        geometry.set_bar_height(70)
        self.texture.set_bar_height()
        self.assertGreater(view.draws, before)

    def test_timer_runs_only_while_a_view_is_shown(self):
        self.assertEqual(self.texture.source, 0)
        view = FakeView(bar_texture.corner_rect(False))
        self.texture.add_view(view)
        self.assertNotEqual(self.texture.source, 0)
        self.texture.remove_view(view)
        self.assertEqual(self.texture.source, 0)

    def test_disabled_animations_stop_the_timer_and_freeze_the_picture(self):
        view = FakeView(bar_texture.corner_rect(False))
        self.texture.settings.set_property("gtk-enable-animations", False)
        self.texture.add_view(view)
        self.assertEqual(self.texture.source, 0)
        first = bytes(self.texture.surface.get_data())
        self.texture.sync()
        self.assertEqual(first, bytes(self.texture.surface.get_data()))
        self.assertGreater(view.draws, 0)

    def test_static_scene_needs_no_timer(self):
        texture = bar_texture.BarTexture(scenes.Solid((0, 0, 0)))
        view = FakeView(bar_texture.corner_rect(False))
        texture.add_view(view)
        self.assertEqual(texture.source, 0)
        texture.remove_view(view)

    def test_renders_only_what_a_view_shows(self):
        view = FakeView(bar_texture.corner_rect(False))
        self.texture.add_view(view)
        self.texture.render(3.0)
        self.assertEqual(alpha_at(self.texture, 10, 10), 255)            # v päte
        self.assertEqual(alpha_at(self.texture, 300, 150), 0)            # v kmeni, ktorý nikto neukazuje

    def test_all_views_get_redrawn_from_one_render(self):
        foot = FakeView(bar_texture.corner_rect(False))
        trunk = FakeView((0, BAR_HEIGHT, TEXTURE_WIDTH, 110))
        self.texture.add_view(foot)
        self.texture.add_view(trunk)
        before = (foot.draws, trunk.draws)
        self.texture.render(2.0)
        self.assertEqual((foot.draws, trunk.draws), (before[0] + 1, before[1] + 1))
        self.assertEqual(alpha_at(self.texture, 300, 150), 255)          # kmeň sa už kreslí

    def test_dim_is_baked_into_the_canvas(self):
        """Text na kmeni je čitateľný: pod ním je textúra stmavená priamo v plátne."""
        plain = bar_texture.BarTexture(scenes.Solid((0.5, 0.5, 0.5)), dim=0)
        dimmed = bar_texture.BarTexture(scenes.Solid((0.5, 0.5, 0.5)), dim=0.8)
        for texture in (plain, dimmed):
            texture.add_view(FakeView(bar_texture.trunk_rect()))
            texture.render(1.0)

        def red(texture):
            texture.surface.flush()
            _px, py, _pw, _ph = texture.pixel_rect((600, 150, 1, 1))
            return texture.surface.get_data()[py * texture.surface.get_stride() + 600 * 4 + 2]
        self.assertLess(red(dimmed), red(plain))

    def test_dim_darkens_the_right_corner_too(self):
        """Zrkadlené prevody nesmú pokaziť tmavý prechod pravého rohu."""
        def level(dim):
            texture = bar_texture.BarTexture(scenes.Solid((0.8, 0.8, 0.8)), right=True, dim=dim)
            texture.add_view(FakeView(bar_texture.corner_rect(True)))
            texture.render(1.0)
            texture.surface.flush()
            x, y_up = TEXTURE_WIDTH - 20, 5                          # spodok päty pri pravom okraji (popis)
            _px, py, _pw, _ph = texture.pixel_rect((x, y_up, 1, 1))
            return texture.surface.get_data()[py * texture.surface.get_stride() + x * 4 + 2]
        self.assertLess(level(0.9), level(0.0))

    def test_real_right_corner_scene_is_dimmed_at_the_label(self):
        def level(dim):
            texture = bar_texture.build(bar_texture.Config(left="solid:motív", right="scene:gears", dim=dim))["resources"]
            texture.add_view(FakeView(bar_texture.corner_rect(True)))
            texture.render(6.0)
            texture.surface.flush()
            data, stride = texture.surface.get_data(), texture.surface.get_stride()
            total = 0
            for x in range(TEXTURE_WIDTH - 150, TEXTURE_WIDTH - 10, 5):
                _px, py, _pw, _ph = texture.pixel_rect((x, 4, 1, 1))
                total += data[py * stride + x * 4 + 2]
            return total
        self.assertLess(level(0.9), level(0.0) * 0.6)

    def test_a_scene_problem_is_reported_once(self):
        from latte_common import filescene
        reports = []
        texture = bar_texture.BarTexture(filescene.FileScene("/nie/je/taky.gif", threaded=False), name="bars.left",
                                         report=reports.append)
        texture.add_view(FakeView(bar_texture.corner_rect(False)))
        for t in (1.0, 2.0, 3.0):
            texture.render(t)
        self.assertEqual(len(reports), 1)
        self.assertTrue(reports[0].startswith("bars.left: "))
        self.assertIn("taky.gif", reports[0])
        texture.remove_view(texture.views[0])

    def test_motion_off_never_runs_a_timer(self):
        texture = bar_texture.BarTexture(scenes.Matrix(), motion="off")
        view = FakeView(bar_texture.corner_rect(False))
        texture.add_view(view)
        self.assertEqual(texture.source, 0)
        self.assertGreater(view.draws, 0)                   # statický snímok sa nakreslil
        texture.remove_view(view)

    def test_hover_mode_moves_only_under_the_pointer_or_with_an_open_popup(self):
        texture = bar_texture.BarTexture(scenes.Matrix(), motion="hover")
        foot = FakeView(bar_texture.corner_rect(False))
        texture.add_view(foot)
        self.assertEqual(texture.source, 0)
        texture.set_hovered(True)
        self.assertNotEqual(texture.source, 0)
        texture.set_hovered(False)
        self.assertEqual(texture.source, 0)
        trunk = FakeView(bar_texture.trunk_rect())
        trunk.awake = True
        texture.add_view(trunk)                              # otvorený popup
        self.assertNotEqual(texture.source, 0)
        texture.remove_view(trunk)
        self.assertEqual(texture.source, 0)
        texture.remove_view(foot)

    def test_always_ignores_the_pointer(self):
        texture = bar_texture.BarTexture(scenes.Matrix(), motion="always")
        view = FakeView(bar_texture.corner_rect(False))
        texture.add_view(view)
        self.assertNotEqual(texture.source, 0)
        texture.set_hovered(False)
        self.assertNotEqual(texture.source, 0)
        texture.remove_view(view)


class ConfigTest(unittest.TestCase):
    def test_defaults_match_the_schema(self):
        import tomllib
        path = os.path.join(os.path.dirname(__file__), "..", "data", "settings", "appearance.schema.toml")
        with open(path, "rb") as f:
            keys = tomllib.load(f)["key"]
        config = bar_texture.Config()
        self.assertEqual(config.left, keys["bars.left"]["default"])
        self.assertEqual(config.right, keys["bars.right"]["default"])
        self.assertEqual(config.motion, keys["bars.motion"]["default"])
        self.assertEqual(config.speed, keys["bars.speed"]["default"])
        self.assertEqual(config.dim, keys["bars.dim"]["default"])
        self.assertEqual(sorted(keys["bars.motion"]["choices"]), sorted(bar_texture.MOTIONS))

    def test_from_values(self):
        config = bar_texture.Config.from_values({"bars.left": "scene:glow", "bars.right": "solid:motív",
                                                 "bars.motion": "hover", "bars.speed": 0.5, "bars.dim": 0.3})
        self.assertEqual((config.left, config.right, config.motion, config.speed, config.dim),
                         ("scene:glow", "solid:motív", "hover", 0.5, 0.3))

    def test_unknown_source_falls_back_and_is_reported(self):
        reports = []
        config = bar_texture.Config.from_values({"bars.left": "scene:nic", "bars.right": ""}, report=reports.append)
        self.assertEqual((config.left, config.right), (bar_texture.DEFAULT_LEFT, bar_texture.DEFAULT_RIGHT))
        self.assertEqual(len(reports), 2)
        self.assertIn("bars.left", reports[0])

    def test_unknown_motion_falls_back_to_always(self):
        self.assertEqual(bar_texture.Config.from_values({"bars.motion": "sometimes"}).motion, "always")

    def test_equal_configs_mean_nothing_to_rebuild(self):
        values = {"bars.left": "scene:glow"}
        self.assertEqual(bar_texture.Config.from_values(values), bar_texture.Config.from_values(dict(values)))
        self.assertNotEqual(bar_texture.Config.from_values(values),
                            bar_texture.Config.from_values(values, palette=scenes.Palette((0, 0, 0), (1, 1, 1))))

    def test_build_makes_textures_for_scenes_only(self):
        built = bar_texture.build(bar_texture.Config(left="scene:matrix", right="solid:motív"))
        self.assertEqual(list(built), ["apps"])
        self.assertFalse(built["apps"].right)
        both = bar_texture.build(bar_texture.Config(left="scene:glow", right="scene:gears", dim=0.4, motion="hover"))
        self.assertEqual(sorted(both), ["apps", "resources"])
        self.assertTrue(both["resources"].right)
        self.assertEqual((both["apps"].dim, both["apps"].motion), (0.4, "hover"))
        self.assertIsInstance(both["resources"].scene, scenes.Gears)
        self.assertTrue(both["resources"].scene.right)

    def test_file_source_builds_a_file_scene(self):
        from latte_common import filescene
        built = bar_texture.build(bar_texture.Config(left="file:/x/a.gif", right="solid:motív"))
        self.assertIsInstance(built["apps"].scene, filescene.FileScene)
        self.assertEqual(built["apps"].name, "bars.left")

    def test_default_build_gives_both_corners_a_texture(self):
        self.assertEqual(sorted(bar_texture.build()), ["apps", "resources"])


if __name__ == "__main__":
    unittest.main()
