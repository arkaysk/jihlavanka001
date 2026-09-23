import errno
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import fileops  # noqa: E402


def write(path, data=b"x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def read(path):
    with open(path, "rb") as f:
        return f.read()


class TransferTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        self.src = os.path.join(self.tmp, "src")
        self.dst = os.path.join(self.tmp, "dst")
        os.makedirs(self.dst)

    def tearDown(self):
        self._tmp.cleanup()

    def run_transfer(self, kind, sources, **kw):
        job = fileops.Transfer(kind, sources, self.dst, **kw)
        events = []
        job.run(events.append)
        return job, events

    def test_copy_files_and_tree(self):
        write(self.src + "/a.txt", b"A" * 10)
        write(self.src + "/d/b.txt", b"B" * 20)
        write(self.src + "/d/sub/c.txt", b"C" * 30)
        os.symlink("a.txt", self.src + "/link")
        job, events = self.run_transfer("copy", [self.src + "/a.txt", self.src + "/d", self.src + "/link"])
        self.assertEqual(job.result.state, "done")
        self.assertEqual(read(self.dst + "/a.txt"), b"A" * 10)
        self.assertEqual(read(self.dst + "/d/sub/c.txt"), b"C" * 30)
        self.assertTrue(os.path.islink(self.dst + "/link"))
        self.assertEqual(os.readlink(self.dst + "/link"), "a.txt")
        self.assertTrue(os.path.exists(self.src + "/a.txt"))
        last = events[-1]
        self.assertEqual((last.bytes_done, last.bytes_total), (60, 60))
        self.assertEqual((last.items_done, last.items_total), (3, 3))
        self.assertEqual(job.result.done, [self.src + "/a.txt", self.src + "/d", self.src + "/link"])

    def test_move_same_device_renames(self):
        write(self.src + "/a.txt", b"A")
        write(self.src + "/d/b.txt", b"B")
        inode = os.stat(self.src + "/a.txt").st_ino
        job, _ = self.run_transfer("move", [self.src + "/a.txt", self.src + "/d"])
        self.assertEqual(job.result.state, "done")
        self.assertFalse(os.path.exists(self.src + "/a.txt"))
        self.assertEqual(os.stat(self.dst + "/a.txt").st_ino, inode)
        self.assertEqual(read(self.dst + "/d/b.txt"), b"B")
        self.assertEqual(job.bytes_total, 0)

    def test_move_across_devices_copies_then_deletes(self):
        write(self.src + "/d/b.txt", b"B" * 5)
        real = os.rename

        def exdev(a, b):
            raise OSError(errno.EXDEV, "cross-device")

        os.rename = exdev
        try:
            job, _ = self.run_transfer("move", [self.src + "/d"])
        finally:
            os.rename = real
        self.assertEqual(job.result.state, "done")
        self.assertFalse(os.path.exists(self.src + "/d"))
        self.assertEqual(read(self.dst + "/d/b.txt"), b"B" * 5)

    def test_conflict_keep_both(self):
        write(self.src + "/a.txt", b"new")
        write(self.dst + "/a.txt", b"old")
        found = fileops.conflicts([self.src + "/a.txt"], self.dst)
        self.assertEqual(found, [(self.src + "/a.txt", self.dst + "/a.txt")])
        job, _ = self.run_transfer("copy", [self.src + "/a.txt"], policy=fileops.KEEP_BOTH)
        self.assertEqual(read(self.dst + "/a.txt"), b"old")
        self.assertEqual(read(self.dst + "/a (2).txt"), b"new")

    def test_conflict_replace_file(self):
        write(self.src + "/a.txt", b"new")
        write(self.dst + "/a.txt", b"old")
        job, _ = self.run_transfer("copy", [self.src + "/a.txt"], policy=fileops.REPLACE)
        self.assertEqual(read(self.dst + "/a.txt"), b"new")
        self.assertEqual(os.listdir(self.dst), ["a.txt"])

    def test_conflict_replace_never_overwrites_directory(self):
        write(self.src + "/d/new.txt", b"new")
        write(self.dst + "/d/old.txt", b"old")
        job, _ = self.run_transfer("copy", [self.src + "/d"], policy=fileops.REPLACE)
        self.assertEqual(read(self.dst + "/d/old.txt"), b"old")
        self.assertEqual(read(self.dst + "/d (2)/new.txt"), b"new")

    def test_conflict_skip(self):
        write(self.src + "/a.txt", b"new")
        write(self.src + "/b.txt", b"b")
        write(self.dst + "/a.txt", b"old")
        job, _ = self.run_transfer("copy", [self.src + "/a.txt", self.src + "/b.txt"], policy=fileops.SKIP)
        self.assertEqual(read(self.dst + "/a.txt"), b"old")
        self.assertEqual(read(self.dst + "/b.txt"), b"b")
        self.assertEqual(job.result.state, "done")

    def test_copy_into_same_folder_makes_numbered_copy(self):
        write(self.dst + "/a.txt", b"A")
        job = fileops.Transfer("copy", [self.dst + "/a.txt"], self.dst)
        job.run()
        self.assertEqual(read(self.dst + "/a (2).txt"), b"A")

    def test_move_into_same_folder_is_noop(self):
        write(self.dst + "/a.txt", b"A")
        job = fileops.Transfer("move", [self.dst + "/a.txt"], self.dst)
        job.run()
        self.assertEqual(os.listdir(self.dst), ["a.txt"])
        self.assertEqual(job.result.state, "done")

    def test_directory_into_itself_refused(self):
        write(self.src + "/d/x.txt")
        job = fileops.Transfer("copy", [self.src + "/d"], self.src + "/d")
        job.run()
        self.assertEqual(job.result.state, "error")
        self.assertEqual(job.result.error[1], errno.EINVAL)
        job = fileops.Transfer("copy", [self.src + "/d"], self.src + "/d/x")
        os.makedirs(self.src + "/d/x")
        job.run()
        self.assertEqual(job.result.state, "error")

    def test_cancel_removes_partial_copy(self):
        write(self.src + "/big/one.bin", b"1" * (3 * fileops.CHUNK))
        write(self.src + "/big/two.bin", b"2" * (3 * fileops.CHUNK))
        job = fileops.Transfer("copy", [self.src + "/big"], self.dst)

        def stop(progress):
            if progress.bytes_done >= fileops.CHUNK:
                job.cancel()

        fileops.PROGRESS_EVERY, old = 0, fileops.PROGRESS_EVERY
        try:
            job.run(stop)
        finally:
            fileops.PROGRESS_EVERY = old
        self.assertEqual(job.result.state, "cancelled")
        self.assertEqual(os.listdir(self.dst), [])
        self.assertTrue(os.path.exists(self.src + "/big/one.bin"))
        self.assertEqual(job.result.done, [])

    def test_cancelled_move_keeps_source(self):
        write(self.src + "/big/one.bin", b"1" * (3 * fileops.CHUNK))
        job = fileops.Transfer("move", [self.src + "/big"], self.dst)
        real = os.rename
        os.rename = lambda a, b: (_ for _ in ()).throw(OSError(errno.EXDEV, "x"))
        fileops.PROGRESS_EVERY, old = 0, fileops.PROGRESS_EVERY
        try:
            job.run(lambda p: job.cancel() if p.bytes_done else None)
        finally:
            os.rename = real
            fileops.PROGRESS_EVERY = old
        self.assertEqual(job.result.state, "cancelled")
        self.assertTrue(os.path.exists(self.src + "/big/one.bin"))
        self.assertEqual(os.listdir(self.dst), [])

    def test_error_stops_and_reports_done_items(self):
        write(self.src + "/a.txt", b"A")
        write(self.src + "/c.txt", b"C")
        job, _ = self.run_transfer("copy", [self.src + "/a.txt", self.src + "/missing", self.src + "/c.txt"])
        self.assertEqual(job.result.state, "error")
        path, code, _msg = job.result.error
        self.assertEqual((path, code), (self.src + "/missing", errno.ENOENT))

    def test_error_reports_permission(self):
        if os.geteuid() == 0:
            self.skipTest("root obchádza práva")
        write(self.src + "/a.txt", b"A")
        os.chmod(self.dst, 0o500)
        try:
            job, _ = self.run_transfer("copy", [self.src + "/a.txt"])
        finally:
            os.chmod(self.dst, 0o700)
        self.assertEqual(job.result.state, "error")
        self.assertEqual(job.result.error[1], errno.EACCES)
        self.assertEqual(job.result.done, [])

    def test_unique_target_keeps_dotfiles_whole(self):
        write(self.dst + "/.bashrc")
        self.assertEqual(fileops.unique_target(self.dst, ".bashrc"), self.dst + "/.bashrc (2)")

    def test_owner_is_applied(self):
        if os.geteuid() != 0:
            self.skipTest("chown vyžaduje root")
        write(self.src + "/d/a.txt")
        job, _ = self.run_transfer("copy", [self.src + "/d"], owner=(1000, 1000))
        self.assertEqual(os.stat(self.dst + "/d").st_uid, 1000)
        self.assertEqual(os.stat(self.dst + "/d/a.txt").st_gid, 1000)


if __name__ == "__main__":
    unittest.main()
