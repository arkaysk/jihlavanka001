"""Náhľady fotiek a videí pre správcu súborov (zobrazenie Miniatúry).

Fotky sa zmenšujú priamo cez GdkPixbuf, videá cez externý thumbnailer podľa štandardných
súborov *.thumbnailer (napr. ffmpegthumbnailer). Práca beží vo vláknach; výsledok príde
v hlavnom vlákne GLib. Výsledky externých thumbnailerov sa ukladajú do ~/.cache/latteos/.
"""
import hashlib
import os
import shlex
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

import gi
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gio, GLib, GdkPixbuf  # noqa: E402

CACHE_DIR = os.path.join(os.path.expanduser("~/.cache"), "latteos", "thumbnails")
THUMBNAILER_DIRS = [
    os.path.expanduser("~/.local/share/thumbnailers"),
    "/usr/local/share/thumbnailers",
    "/usr/share/thumbnailers",
]
MAX_IMAGE_BYTES = 100 * 1024 * 1024
THUMBNAILER_TIMEOUT = 20

_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="thumb")
_thumbnailers = None            # mime -> [(TryExec, Exec)]


def content_type(path):
    ctype, _uncertain = Gio.content_type_guess(path, None)
    return ctype or ""


def wants_thumbnail(path):
    """Len fotky a videá; ostatné súbory ostanú pri ikone svojho druhu."""
    ctype = content_type(path)
    return ctype.startswith(("image/", "video/"))


def _load_thumbnailers():
    global _thumbnailers
    if _thumbnailers is not None:
        return _thumbnailers
    found = {}
    for directory in THUMBNAILER_DIRS:
        try:
            names = sorted(os.listdir(directory))
        except OSError:
            continue
        for name in names:
            if not name.endswith(".thumbnailer"):
                continue
            key = GLib.KeyFile()
            try:
                key.load_from_file(os.path.join(directory, name), GLib.KeyFileFlags.NONE)
                command = key.get_string("Thumbnailer Entry", "Exec")
                mimes = key.get_string_list("Thumbnailer Entry", "MimeType")
            except GLib.Error:
                continue
            try:
                try_exec = key.get_string("Thumbnailer Entry", "TryExec")
            except GLib.Error:
                try_exec = ""               # TryExec je nepovinný
            for mime in mimes:
                found.setdefault(mime, []).append((try_exec, command))
    _thumbnailers = found
    return found


def _thumbnailer_for(ctype):
    for try_exec, command in _load_thumbnailers().get(ctype, []):
        binary = try_exec or shlex.split(command)[0]
        if shutil.which(binary):
            return command
    return None


def _cache_file(path, size):
    st = os.stat(path)
    digest = hashlib.sha1(("%s|%d|%d|%d" % (path, st.st_mtime_ns, st.st_size, size)).encode()).hexdigest()
    return os.path.join(CACHE_DIR, "%s-%d.png" % (digest, size))


def _run_thumbnailer(command, path, size):
    """Vráti cestu k PNG s náhľadom (z medzipamäte alebo čerstvo vytvoreným), alebo None."""
    cached = _cache_file(path, size)
    if os.path.exists(cached):
        return cached
    os.makedirs(CACHE_DIR, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".png", dir=CACHE_DIR)
    os.close(fd)
    args = []
    for part in shlex.split(command):
        part = (part.replace("%i", path).replace("%u", Gio.File.new_for_path(path).get_uri())
                .replace("%o", tmp).replace("%s", str(size)).replace("%%", "%"))
        args.append(part)
    try:
        subprocess.run(args, capture_output=True, timeout=THUMBNAILER_TIMEOUT, check=True)
        if os.path.getsize(tmp) > 0:
            os.replace(tmp, cached)
            return cached
    except (subprocess.SubprocessError, OSError):
        pass
    try:
        os.unlink(tmp)
    except OSError:
        pass
    return None


def _make(path, size):
    """GdkPixbuf.Pixbuf s náhľadom súboru, alebo None (súbor sa nedá zobraziť ako miniatúra)."""
    ctype = content_type(path)
    try:
        if ctype.startswith("image/"):
            if os.path.getsize(path) > MAX_IMAGE_BYTES:
                return None
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, size, size, True)
            return pixbuf.apply_embedded_orientation() or pixbuf
        if ctype.startswith("video/"):
            command = _thumbnailer_for(ctype)
            if command is None:
                return None
            png = _run_thumbnailer(command, path, size)
            return GdkPixbuf.Pixbuf.new_from_file_at_scale(png, size, size, True) if png else None
    except (GLib.Error, OSError):
        return None
    return None


def video_thumbnails_available():
    """Je nainštalovaný thumbnailer pre videá? (na upozornenie v správcovi súborov)"""
    return any(_thumbnailer_for(m) for m in _load_thumbnailers() if m.startswith("video/"))


def request(path, size, on_ready, alive=lambda: True):
    """Vo vlákne pripraví náhľad; on_ready(pixbuf | None) sa zavolá v hlavnom vlákne,
    ak je alive() stále pravda (panel medzitým nezmenil priečinok)."""
    _load_thumbnailers()                        # načítanie *.thumbnailer v hlavnom vlákne

    def work():
        if not alive():
            return
        pixbuf = _make(path, size)
        GLib.idle_add(lambda: (on_ready(pixbuf) if alive() else None, False)[1])

    _pool.submit(work)
