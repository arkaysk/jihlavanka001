import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import cairo  # noqa: E402

from latte_common import scenes  # noqa: E402
from latte_shell import bar_texture  # noqa: E402
from latte_shell.geometry import BAR_HEIGHT, CORNER_WIDTH, TEXTURE_HEIGHT, TEXTURE_WIDTH  # noqa: E402


class FakeView:
    def __init__(self, rect):
        self.rect = rect
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
        self.animations = self.texture.settings.get_property("gtk-enable-animations")

    def tearDown(self):
        for view in list(self.texture.views):
            self.texture.remove_view(view)
        self.texture.settings.set_property("gtk-enable-animations", self.animations)

    def test_canvas_origin_is_the_screen_corner_and_y_goes_up(self):
        self.assertEqual(self.texture.pixel_rect((0, 0, CORNER_WIDTH, BAR_HEIGHT)),
                         (0, TEXTURE_HEIGHT - BAR_HEIGHT, CORNER_WIDTH, BAR_HEIGHT))

    def test_corner_rects(self):
        self.assertEqual(bar_texture.corner_rect(False), (0, 0, CORNER_WIDTH, BAR_HEIGHT))
        self.assertEqual(bar_texture.corner_rect(True), (TEXTURE_WIDTH - CORNER_WIDTH, 0, CORNER_WIDTH, BAR_HEIGHT))

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

    def test_build_skips_plain_tiles_and_unknown_sources(self):
        built = bar_texture.build({"apps": "scene:matrix", "resources": None, "x": "scene:nic"})
        self.assertEqual(list(built), ["apps"])


if __name__ == "__main__":
    unittest.main()
