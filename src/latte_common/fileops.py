"""Súborové operácie LatteOS: kopírovanie, presun a mazanie s priebehom a zrušením.

Bez GTK. Beží vo vlákne správcu súborov, alebo ako root v latte-files-admin
(tam sa tento súbor nainštaluje vedľa skriptu).
"""
import errno
import os
import shutil
import stat
import time
from collections import namedtuple

CHUNK = 1024 * 1024
PROGRESS_EVERY = 0.05           # s medzi hláseniami priebehu

KEEP_BOTH, REPLACE, SKIP = "keep_both", "replace", "skip"

Progress = namedtuple("Progress", "bytes_done bytes_total items_done items_total current")


class Cancelled(Exception):
    pass


class TransferError(Exception):
    def __init__(self, path, err):
        super().__init__(path)
        self.path = path
        self.errno = getattr(err, "errno", None) or errno.EIO
        self.message = getattr(err, "strerror", None) or str(err)


class Result:
    """state: done | cancelled | error. done = zdroje, ktoré sú celé hotové."""

    def __init__(self):
        self.state = "done"
        self.done = []
        self.error = None       # (cesta, errno, správa)


def unique_target(dest_dir, name):
    """„foto.jpg“ -> „foto (2).jpg“, kým nie je meno voľné."""
    stem, ext = os.path.splitext(name)
    if name.startswith(".") and not ext:
        stem, ext = name, ""
    n = 2
    while True:
        candidate = os.path.join(dest_dir, "%s (%d)%s" % (stem, n, ext))
        if not os.path.lexists(candidate):
            return candidate
        n += 1


def is_real_dir(path):
    return os.path.isdir(path) and not os.path.islink(path)


def remove_tree(path):
    if is_real_dir(path):
        shutil.rmtree(path)
    else:
        os.unlink(path)


def conflicts(sources, dest_dir):
    """Zdroje, ktorých meno v cieli už existuje: [(zdroj, existujúci cieľ)]."""
    found = []
    for src in sources:
        dst = os.path.join(dest_dir, os.path.basename(src))
        if os.path.lexists(dst) and os.path.abspath(src) != os.path.abspath(dst):
            found.append((src, dst))
    return found


def tree_size(path):
    """Počet bajtov súborov pod cestou (symlinky sa nasledujú len ako odkaz)."""
    try:
        st = os.lstat(path)
    except OSError:
        return 0
    if stat.S_ISREG(st.st_mode):
        return st.st_size
    if not stat.S_ISDIR(st.st_mode):
        return 0
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                total += tree_size(entry.path)
    except OSError:
        pass
    return total


class Transfer:
    """kind: "copy" | "move". policy platí pre všetky konflikty mien v cieli.

    owner = (uid, gid): nové položky dostanú tohto vlastníka (pri behu ako root).
    run() je blokujúce, notify(Progress) sa volá z vlákna, v ktorom beží.
    """

    def __init__(self, kind, sources, dest_dir, policy=KEEP_BOTH, owner=None):
        self.kind = kind
        self.sources = list(sources)
        self.dest_dir = dest_dir
        self.policy = policy
        self.owner = owner
        self.result = Result()
        self._skipped = []
        self._cancel = False
        self._notify = None
        self._last = 0.0
        self.bytes_done = 0
        self.bytes_total = 0
        self.items_done = 0
        self.items_total = 0
        self.current = ""

    def cancel(self):
        self._cancel = True

    # -------- beh --------
    def run(self, notify=None):
        self._notify = notify
        try:
            pairs = self._prepare()
            self.items_total = len(pairs)
            self._emit(force=True)
            for src, dst, replace, renamed in pairs:
                self._check_cancel()
                self.current = os.path.basename(src)
                self._emit(force=True)
                self._one(src, dst, replace, renamed)
                self.result.done.append(src)
                self.items_done += 1
            # zdroje preskočené kvôli konfliktu (SKIP) sú tiež vybavené
            self.result.done = [s for s in self.sources if s in self.result.done or s in self._skipped]
        except Cancelled:
            self.result.state = "cancelled"
        except TransferError as err:
            self.result.state = "error"
            self.result.error = (err.path, err.errno, err.message)
        except OSError as err:          # poistka: vlákno nikdy nesmie skončiť bez výsledku
            self.result.state = "error"
            self.result.error = (err.filename or self.dest_dir, err.errno or errno.EIO, err.strerror or str(err))
        self._emit(force=True)
        return self.result

    def _check_cancel(self):
        if self._cancel:
            raise Cancelled()

    def _emit(self, force=False):
        if self._notify is None:
            return
        now = time.monotonic()
        if not force and now - self._last < PROGRESS_EVERY:
            return
        self._last = now
        self._notify(Progress(self.bytes_done, self.bytes_total,
                              self.items_done, self.items_total, self.current))

    # -------- príprava --------
    def _prepare(self):
        pairs = []
        dest_real = os.path.realpath(self.dest_dir)
        try:
            dest_dev = os.stat(self.dest_dir).st_dev
        except OSError as err:
            raise TransferError(self.dest_dir, err)

        for src in self.sources:
            try:
                st = os.lstat(src)
            except OSError as err:
                raise TransferError(src, err)
            if stat.S_ISDIR(st.st_mode):
                src_real = os.path.realpath(src)
                if dest_real == src_real or dest_real.startswith(src_real + os.sep):
                    raise TransferError(src, OSError(errno.EINVAL, "Priečinok sa nedá vložiť sám do seba"))

            dst = os.path.join(self.dest_dir, os.path.basename(src))
            replace = False
            renamed = False
            if os.path.abspath(src) == os.path.abspath(dst):
                if self.kind == "move":
                    self._skipped.append(src)
                    continue
                dst, renamed = unique_target(self.dest_dir, os.path.basename(src)), True
            elif os.path.lexists(dst):
                if self.policy == SKIP:
                    self._skipped.append(src)
                    continue
                if self.policy == REPLACE and not is_real_dir(dst) and not stat.S_ISDIR(st.st_mode):
                    replace = True
                else:
                    # priečinky sa nikdy neprepisujú: ponechať obe
                    dst, renamed = unique_target(self.dest_dir, os.path.basename(src)), True

            by_rename = self.kind == "move" and st.st_dev == dest_dev
            pairs.append((src, dst, replace, renamed))
            if not by_rename:
                self.bytes_total += tree_size(src)
        return pairs

    # -------- jedna položka --------
    def _one(self, src, dst, replace, renamed):
        if replace:
            self._delete(dst)
        if self.kind == "move":
            try:
                os.rename(src, dst)
                return
            except OSError as err:
                if err.errno != errno.EXDEV:
                    raise TransferError(src, err)
            self._copy_out(src, dst)
            self._delete(src)
        else:
            self._copy_out(src, dst)

    def _copy_out(self, src, dst):
        """Skopíruje; pri zrušení či chybe odstráni rozpracovanú kópiu (cieľ predtým neexistoval)."""
        try:
            self._copy(src, dst)
        except (Cancelled, TransferError):
            try:
                if os.path.lexists(dst):
                    remove_tree(dst)
            except OSError:
                pass
            raise

    def _delete(self, path):
        try:
            remove_tree(path)
        except OSError as err:
            raise TransferError(path, err)

    def _own(self, path):
        if self.owner is not None:
            try:
                os.chown(path, self.owner[0], self.owner[1], follow_symlinks=False)
            except OSError as err:
                raise TransferError(path, err)

    def _copy(self, src, dst):
        self._check_cancel()
        try:
            st = os.lstat(src)
            if stat.S_ISLNK(st.st_mode):
                os.symlink(os.readlink(src), dst)
                self._own(dst)
            elif stat.S_ISDIR(st.st_mode):
                os.mkdir(dst)
                self._own(dst)
                with os.scandir(src) as it:
                    entries = sorted(it, key=lambda e: e.name)
                for entry in entries:
                    self._copy(entry.path, os.path.join(dst, entry.name))
                shutil.copystat(src, dst)
            elif stat.S_ISREG(st.st_mode):
                self._copy_file(src, dst)
            # súbory zariadení, sokety a rúry sa nekopírujú
        except OSError as err:
            raise TransferError(src, err)

    def _copy_file(self, src, dst):
        with open(src, "rb") as fin:
            fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as fout:
                self._own(dst)
                while True:
                    self._check_cancel()
                    chunk = fin.read(CHUNK)
                    if not chunk:
                        break
                    fout.write(chunk)
                    self.bytes_done += len(chunk)
                    self._emit()
        shutil.copystat(src, dst)
        self._emit()
