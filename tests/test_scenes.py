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


if __name__ == "__main__":
    unittest.main()
