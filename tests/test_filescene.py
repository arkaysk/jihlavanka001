import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import cairo  # noqa: E402
import gi  # noqa: E402
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, GLib  # noqa: E402

import animfiles  # noqa: E402
from latte_common import filescene, scenes  # noqa: E402

RED, GREEN, BLUE = (255, 0, 0), (0, 255, 0), (0, 0, 255)


def sync(*args, **kw):
    """FileScene, ktorá načíta hneď (bez vlákna a hlavnej slučky)."""
    return filescene.FileScene(*args, threaded=False, **kw)


def pixel(scene, x, y, t=0.0, width=40, height=20):
    """RGB pixelu (x, y) plátna width x height v čase t (cairo BGRA)."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    scene.render(cairo.Context(surface), width, height, t)
    surface.flush()
    data, stride = surface.get_data(), surface.get_stride()
    b, g, r, a = data[y * stride + x * 4:y * stride + x * 4 + 4]
    return (r, g, b)


class FileTestCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)

    def path(self, name):
        return os.path.join(self._dir.name, name)

    def gif(self, frames, delays, name="a.gif", **kw):
        path = self.path(name)
        animfiles.make_gif(path, frames, delays, **kw)
        return path


class FramesTextTest(unittest.TestCase):
    def test_slovak_plural(self):
        expected = {1: "1 snímka", 2: "2 snímky", 3: "3 snímky", 4: "4 snímky", 5: "5 snímok", 11: "11 snímok",
                    12: "12 snímok", 14: "14 snímok", 21: "21 snímok", 22: "22 snímky", 40: "40 snímok",
                    101: "101 snímok", 102: "102 snímky"}
        for count, text in expected.items():
            self.assertEqual(filescene.frames_text(count), text, count)


class HeaderParsingTest(FileTestCase):
    def read(self, path):
        with open(path, "rb") as f:
            return f.read()

    def test_gif_durations_come_from_the_headers(self):
        path = self.gif([RED, GREEN, BLUE], [10, 20, 30])
        self.assertEqual(filescene.gif_durations(self.read(path)), [100, 200, 300])

    def test_zero_or_one_hundredth_delay_means_a_tenth_of_a_second(self):
        path = self.gif([RED, GREEN, BLUE], [0, 1, 5])
        self.assertEqual(filescene.gif_durations(self.read(path)), [100, 100, 50])

    def test_not_a_gif_is_none(self):
        for data in (b"", b"GIF89a", b"hello world, this is not an image", b"\x89PNG\r\n\x1a\n" + b"0" * 30):
            self.assertIsNone(filescene.gif_durations(data))

    def test_truncated_gif_does_not_crash(self):
        data = self.read(self.gif([RED, GREEN], [10, 10]))
        for cut in (14, 30, 800, len(data) - 5):
            filescene.gif_durations(data[:cut])              # nesmie vyhodiť výnimku

    def riff(self, chunks):
        body = b"WEBP" + b"".join(tag + struct.pack("<I", len(payload)) + payload + (b"\0" if len(payload) & 1 else b"")
                                  for tag, payload in chunks)
        return b"RIFF" + struct.pack("<I", len(body)) + body

    def anmf(self, ms):
        return b"ANMF", b"\0" * 12 + ms.to_bytes(3, "little") + b"\0" + b"\0" * 4

    def test_webp_durations(self):
        data = self.riff([(b"VP8X", bytes([0x02]) + b"\0" * 9), self.anmf(120), self.anmf(80), self.anmf(0)])
        self.assertEqual(filescene.webp_durations(data), [120, 80, 100])

    def test_still_webp_and_not_webp(self):
        self.assertEqual(filescene.webp_durations(self.riff([(b"VP8X", bytes([0x00]) + b"\0" * 9)])), [])
        self.assertIsNone(filescene.webp_durations(b"RIFF\0\0\0\0WAVEfmt "))

    def test_sniff(self):
        self.assertEqual(filescene.sniff(b"GIF89a....."), "gif")
        self.assertEqual(filescene.sniff(self.riff([(b"VP8X", b"\0" * 10)])), "webp")
        self.assertIsNone(filescene.sniff(b"\x89PNG"))


class ParseTest(unittest.TestCase):
    def test_file_sources(self):
        scene = scenes.parse("file:/home/u/a.gif", speed=0.5)
        self.assertIsInstance(scene, filescene.FileScene)
        self.assertEqual((scene.path, scene.speed), ("/home/u/a.gif", 0.5))
        self.assertTrue(scenes.is_known("file:/x.gif"))

    def test_relative_or_empty_path_is_unknown(self):
        for spec in ("file:", "file:a.gif", "file:./a.gif", "file:~/a.gif", "file:/"):
            self.assertIsNone(scenes.parse(spec), spec)
            self.assertFalse(scenes.is_known(spec), spec)

    def test_parse_reads_nothing(self):
        scene = scenes.parse("file:/nie/je/taky/subor.gif")
        self.assertEqual(scene.problem, "")                # problém až pri načítaní


class PlaybackTest(FileTestCase):
    def scene(self, frames, delays, name="a.gif", **kw):
        return sync(self.gif(frames, delays, name=name), **kw)

    def test_frames_follow_time_and_loop(self):
        scene = self.scene([RED, GREEN, BLUE], [10, 20, 30])          # 0,1 s + 0,2 s + 0,3 s = 0,6 s
        colors = {t: pixel(scene, 5, 5, t) for t in (0.02, 0.2, 0.45, 0.62, 0.8)}
        self.assertEqual(colors[0.02], RED)
        self.assertEqual(colors[0.2], GREEN)
        self.assertEqual(colors[0.45], BLUE)
        self.assertEqual(colors[0.62], RED)                            # slučka
        self.assertEqual(colors[0.8], GREEN)

    def test_speed_scales_the_time(self):
        slow = self.scene([RED, GREEN, BLUE], [10, 20, 30], speed=0.5)
        self.assertEqual(pixel(slow, 5, 5, 0.4), GREEN)                # pri rýchlosti 0,5 je t = 0,4 ako 0,2 s

    def test_same_time_same_picture(self):
        scene = self.scene([RED, GREEN], [10, 10])
        self.assertEqual(pixel(scene, 5, 5, 0.15), pixel(scene, 5, 5, 0.15))

    def test_info_and_memory_are_reported(self):
        scene = self.scene([RED, GREEN, BLUE], [10, 20, 30])
        pixel(scene, 5, 5)
        self.assertTrue(scene.animated)
        self.assertEqual(scene.problem, "")
        self.assertEqual(scene.memory, 6 * 20 * 10 * 4)                # 0,6 s pri 10 obr/s, polovičné rozlíšenie 20 x 10
        self.assertIn("6 snímok", scene.info)

    def test_cover_fit_keeps_orientation(self):
        scene = self.scene([(RED, BLUE)], [10], name="halves.gif")     # jeden snímok: vľavo červená, vpravo modrá
        self.assertEqual(pixel(scene, 3, 10), RED)
        self.assertEqual(pixel(scene, 36, 10), BLUE)

    def test_wide_canvas_crops_instead_of_stretching(self):
        """Obraz 2:1 na plátne 4:1: zväčší sa na šírku a ustrihne hore a dole, farby ostanú vľavo a vpravo."""
        scene = self.scene([(RED, BLUE)], [10], name="w.gif")
        self.assertEqual(pixel(scene, 3, 2, width=80, height=20), RED)
        self.assertEqual(pixel(scene, 76, 17, width=80, height=20), BLUE)

    def test_a_single_frame_gif_is_a_still_picture(self):
        scene = self.scene([RED], [10], name="one.gif")
        self.assertEqual(pixel(scene, 5, 5, 3.0), RED)
        self.assertFalse(scene.animated)
        self.assertIn("nehybný", scene.info)

    def test_png_is_a_still_picture(self):
        path = self.path("a.png")
        pb = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 8, 4)
        pb.fill(0x00FF00FF)
        pb.savev(path, "png", [], [])
        scene = sync(path)
        self.assertEqual(pixel(scene, 5, 5), GREEN)
        self.assertFalse(scene.animated)
        self.assertEqual(scene.problem, "")

    def test_reload_only_when_the_canvas_size_changes(self):
        scene = self.scene([RED, GREEN], [10, 10])
        pixel(scene, 1, 1)
        first = scene._frames
        pixel(scene, 1, 1, 0.3)
        self.assertIs(scene._frames, first)
        pixel(scene, 1, 1, 0.3, width=60, height=30)
        self.assertIsNot(scene._frames, first)

    def test_paints_only_inside_the_clip(self):
        scene = self.scene([RED, GREEN], [10, 10])
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 40, 20)
        cr = cairo.Context(surface)
        cr.rectangle(0, 0, 10, 10)
        cr.clip()
        scene.render(cr, 40, 20, 0.0)
        surface.flush()
        self.assertEqual(surface.get_data()[(15 * surface.get_stride() + 30 * 4) + 3], 0)


class BrokenFilesTest(FileTestCase):
    def render_all(self, scene):
        return pixel(scene, 5, 5)                          # nesmie vyhodiť výnimku

    def test_missing_file(self):
        scene = sync(self.path("nie-je.gif"))
        self.render_all(scene)
        self.assertIn("nie-je.gif", scene.problem)
        self.assertFalse(scene.animated)
        for got, want in zip(pixel(scene, 5, 5), filescene.BACKGROUND):
            self.assertAlmostEqual(got, want * 255, delta=1.5)

    def test_not_an_image(self):
        path = self.path("text.gif")
        with open(path, "w") as f:
            f.write("toto nie je obrázok")
        scene = sync(path)
        self.render_all(scene)
        self.assertTrue(scene.problem)
        self.assertFalse(scene.animated)

    def test_a_directory(self):
        scene = sync(self._dir.name)
        self.render_all(scene)
        self.assertTrue(scene.problem)

    def test_truncated_gif_is_reported_or_shown_never_a_crash(self):
        path = self.gif([RED, GREEN, BLUE], [10, 10, 10])
        with open(path, "rb") as f:
            data = f.read()
        cut = self.path("cut.gif")
        with open(cut, "wb") as f:
            f.write(data[:len(data) // 2])
        scene = sync(cut)
        self.render_all(scene)


class BudgetTest(FileTestCase):
    """Rozpočet pamäte: dlhá animácia sa nezmestí, vzorkuje sa redšie alebo sa použije len začiatok, nikdy potichu."""
    W, H = 200, 100                                       # polovičné rozlíšenie 100 x 50 = 20 000 B na snímku

    def long_gif(self, frames=100, delay_cs=10):
        return self.gif([(i * 2 % 256, 0, 0) for i in range(frames)], [delay_cs] * frames, name="long.gif")

    def test_fits_without_a_problem(self):
        scene = sync(self.long_gif(20, 10), budget=20 * 20000)         # 2 s pri 10 obr/s = 20 snímok
        pixel(scene, 1, 1, width=self.W, height=self.H)
        self.assertEqual(scene.problem, "")
        self.assertLessEqual(scene.memory, 20 * 20000)

    def test_a_bit_too_long_is_sampled_less_often_but_plays_fully(self):
        scene = sync(self.long_gif(100, 10), budget=25 * 20000)        # 10 s, smie 25 snímok = 2,5 obr/s
        pixel(scene, 1, 1, width=self.W, height=self.H)
        self.assertLessEqual(scene.memory, 25 * 20000)
        self.assertLessEqual(scene.info.count("snímok"), 1)

    def test_far_too_long_uses_only_the_beginning_and_says_so(self):
        scene = sync(self.long_gif(100, 10), budget=5 * 20000)         # 10 s, smie 5 snímok
        pixel(scene, 1, 1, width=self.W, height=self.H)
        self.assertLessEqual(scene.memory, 5 * 20000)
        self.assertIn("začiatok", scene.problem)
        self.assertTrue(scene.animated)

    def test_memory_never_exceeds_the_budget(self):
        for budget in (20000, 60000, 300000):
            scene = sync(self.long_gif(60, 5), budget=budget)
            pixel(scene, 1, 1, width=self.W, height=self.H)
            self.assertLessEqual(scene.memory, max(budget, 20000), budget)


class ThreadedLoadTest(FileTestCase):
    """Načítanie vo vlákne: hotové je až po odovzdaní hlavnému vláknu; platí len posledná požiadavka."""

    def wait(self, scene, seconds=10.0):
        import time
        end = time.monotonic() + seconds
        context = GLib.MainContext.default()
        while scene.loading and time.monotonic() < end:
            context.iteration(False)
            time.sleep(0.005)
        self.assertFalse(scene.loading, "načítanie neskončilo")

    def test_background_while_loading_then_the_frames(self):
        scene = filescene.FileScene(self.gif([RED, GREEN], [10, 10]))
        self.assertTrue(scene.animated and not scene.loading)         # pred prvým kreslením sa nič nenačítava
        first = pixel(scene, 5, 5)                                     # spustí načítanie
        self.assertTrue(scene.loading or scene.info)                   # vlákno mohlo byť rýchlejšie než kontrola
        for got, want in zip(first, filescene.BACKGROUND):
            if scene.loading:
                self.assertAlmostEqual(got, want * 255, delta=1.5)
        self.wait(scene)
        self.assertEqual(pixel(scene, 5, 5, 0.02), RED)
        self.assertEqual(pixel(scene, 5, 5, 0.12), GREEN)

    def test_result_reaches_the_scene_only_through_the_main_loop(self):
        scene = filescene.FileScene(self.gif([RED, GREEN], [10, 10]))
        pixel(scene, 5, 5)
        import time
        time.sleep(0.5)                                                # vlákno skončilo, ale hlavná slučka nebežala
        self.assertTrue(scene.loading)
        self.assertEqual(scene.info, "")
        self.wait(scene)
        self.assertTrue(scene.info)

    def test_only_the_latest_size_wins(self):
        scene = filescene.FileScene(self.gif([RED, GREEN, BLUE], [10, 10, 10]))
        scene.load(40, 20)
        scene.load(80, 40)                                             # ďalšia požiadavka skôr, než prvá skončí
        self.wait(scene)
        self.assertEqual(scene._size, (80, 40))
        self.assertEqual((scene._frames[0].get_width(), scene._frames[0].get_height()), (40, 20))

    def test_a_problem_in_the_thread_becomes_a_problem_of_the_scene(self):
        scene = filescene.FileScene(self.path("nie-je.gif"))
        pixel(scene, 1, 1)
        self.wait(scene)
        self.assertIn("nie-je.gif", scene.problem)
        self.assertFalse(scene.animated)

    def test_old_frames_stay_visible_while_a_new_size_loads(self):
        scene = filescene.FileScene(self.gif([RED, GREEN], [10, 10]))
        pixel(scene, 1, 1)
        self.wait(scene)
        scene.load(80, 40)
        self.assertTrue(scene._frames)                                 # ešte staré snímky, kreslia sa zväčšené
        self.wait(scene)


if __name__ == "__main__":
    unittest.main()
