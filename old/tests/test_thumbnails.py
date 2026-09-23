import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import gi  # noqa: E402
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf  # noqa: E402

from latte_common import thumbnails  # noqa: E402


def make_png(path, w, h):
    pix = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, w, h)
    pix.fill(0x336699FF)
    pix.savev(path, "png", [], [])


class ThumbnailTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        self._cache = thumbnails.CACHE_DIR
        thumbnails.CACHE_DIR = os.path.join(self.tmp, "cache")

    def tearDown(self):
        thumbnails.CACHE_DIR = self._cache
        self._tmp.cleanup()

    def test_only_photos_and_videos_want_thumbnails(self):
        self.assertTrue(thumbnails.wants_thumbnail("a.jpg"))
        self.assertTrue(thumbnails.wants_thumbnail("b.PNG"))
        self.assertTrue(thumbnails.wants_thumbnail("c.mp4"))
        self.assertTrue(thumbnails.wants_thumbnail("d.mkv"))
        self.assertFalse(thumbnails.wants_thumbnail("e.txt"))
        self.assertFalse(thumbnails.wants_thumbnail("f.pdf"))

    def test_image_is_scaled_keeping_aspect(self):
        path = os.path.join(self.tmp, "wide.png")
        make_png(path, 400, 100)
        pix = thumbnails._make(path, 112)
        self.assertEqual((pix.get_width(), pix.get_height()), (112, 28))

    def test_small_image_is_not_enlarged_beyond_request(self):
        path = os.path.join(self.tmp, "tiny.png")
        make_png(path, 16, 16)
        pix = thumbnails._make(path, 112)
        self.assertLessEqual(max(pix.get_width(), pix.get_height()), 112)

    def test_broken_image_gives_none(self):
        path = os.path.join(self.tmp, "broken.jpg")
        with open(path, "wb") as f:
            f.write(b"toto nie je obrazok")
        self.assertIsNone(thumbnails._make(path, 112))

    def test_missing_file_gives_none(self):
        self.assertIsNone(thumbnails._make(os.path.join(self.tmp, "nie-je.png"), 112))

    @unittest.skipUnless(shutil.which("ffmpegthumbnailer") and shutil.which("gst-launch-1.0"),
                         "chýba ffmpegthumbnailer alebo gst-launch")
    def test_video_thumbnail_and_cache(self):
        video = os.path.join(self.tmp, "clip.ogv")
        proc = subprocess.run(
            ["gst-launch-1.0", "-q", "videotestsrc", "num-buffers=60", "!", "video/x-raw,width=320,height=180,framerate=30/1",
             "!", "theoraenc", "!", "oggmux", "!", "filesink", "location=" + video], capture_output=True)
        if proc.returncode != 0 or not os.path.exists(video):
            self.skipTest("gstreamer nevie vytvoriť skúšobné video: " + proc.stderr.decode()[:100])
        started = time.monotonic()
        pix = thumbnails._make(video, 112)
        self.assertIsNotNone(pix)
        self.assertEqual(pix.get_width(), 112)
        cached = os.listdir(thumbnails.CACHE_DIR)
        self.assertEqual(len(cached), 1)
        mtime = os.stat(os.path.join(thumbnails.CACHE_DIR, cached[0])).st_mtime_ns
        self.assertIsNotNone(thumbnails._make(video, 112))          # druhý raz z medzipamäte
        self.assertEqual(os.stat(os.path.join(thumbnails.CACHE_DIR, cached[0])).st_mtime_ns, mtime)
        self.assertLess(time.monotonic() - started, thumbnails.THUMBNAILER_TIMEOUT)

    def test_video_without_thumbnailer_gives_none(self):
        real = thumbnails._thumbnailers
        thumbnails._thumbnailers = {}
        try:
            path = os.path.join(self.tmp, "v.mp4")
            open(path, "wb").close()
            self.assertIsNone(thumbnails._make(path, 112))
            self.assertFalse(thumbnails.video_thumbnails_available())
        finally:
            thumbnails._thumbnailers = real


if __name__ == "__main__":
    unittest.main()
