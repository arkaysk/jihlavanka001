"""Zdroj textúry zo súboru: animovaný GIF, animované WebP alebo obyčajný obrázok (docs/lista-a-rohy.md, časť 4).

Zápis `file:/absolútna/cesta`. Súbor sa číta až pri prvom kreslení (parse nerobí žiadne I/O), snímky sa
vzorkujú v pevnom čase (najviac MAX_FPS) a ukladajú v **polovičnom rozlíšení plátna**, orezané tak, aby
vyplnili celé plátno (cover). Pamäť je obmedzená rozpočtom (BUDGET_BYTES na jednu animáciu): dlhšia animácia
sa nezmestí ani pri MIN_FPS, preto sa použije len jej začiatok a povie sa to (FileScene.problem), nikdy
potichu.

GdkPixbuf nevie povedať dĺžku slučky, preto sa trvania snímkov čítajú z hlavičiek súboru (gif_durations,
webp_durations). Obraz je čistá funkcia času ako pri kódovaných scénach.

Načítanie (dekódovanie všetkých snímkov) trvá pri veľkom GIF-e aj sekundu a viac, preto beží **vo vlákne**:
kým nie je hotové, scéna kreslí tmavý podklad (loading je pravdivé) a výsledok sa odovzdá hlavnému vláknu cez
GLib.idle_add. Rozmer plátna sa môže zmeniť skôr, než vlákno skončí: platí len posledná požiadavka.
"""
import math
import os
import struct
import threading
import warnings

import cairo
import gi
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, GLib  # noqa: E402

from latte_common.scenes import Scene  # noqa: E402

# GdkPixbuf.PixbufAnimation a jeho iterátor sú v prekrytiach PyGObject označené za zastarané, ale nemajú náhradu
warnings.filterwarnings("ignore", category=DeprecationWarning, message=r"GdkPixbuf\.\w+\.\w+ is deprecated")

MAX_FPS = 10
MIN_FPS = 4
BUDGET_BYTES = 24 * 1024 * 1024
MAX_FILE_BYTES = 128 * 1024 * 1024
BACKGROUND = (0.05, 0.05, 0.05)
DEFAULT_DELAY_MS = 100              # oneskorenie 0 alebo 1 stotina sa v prehliadačoch berie ako 100 ms


def gif_durations(data):
    """Trvanie každého snímku GIF v ms, čítané z hlavičiek; None, ak to nie je platný GIF."""
    if data[:6] not in (b"GIF87a", b"GIF89a") or len(data) < 14:
        return None
    pos = 13
    if data[10] & 0x80:
        pos += 3 * (2 << (data[10] & 7))
    out, delay, n = [], 0, len(data)
    while pos < n:
        marker = data[pos]
        if marker == 0x3B:
            break
        if marker == 0x21:
            if pos + 2 > n:
                return None
            label = data[pos + 1]
            pos += 2
            if label == 0xF9 and pos + 4 <= n:
                delay = struct.unpack_from("<H", data, pos + 1 + 1)[0]
            while pos < n and data[pos]:
                pos += data[pos] + 1
            pos += 1
        elif marker == 0x2C:
            if pos + 10 > n:
                return None
            local = data[pos + 9]
            pos += 10
            if local & 0x80:
                pos += 3 * (2 << (local & 7))
            pos += 1                                            # najmenšia veľkosť kódu LZW
            while pos < n and data[pos]:
                pos += data[pos] + 1
            pos += 1
            out.append((delay if delay > 1 else DEFAULT_DELAY_MS // 10) * 10)
            delay = 0
        else:
            return None
    return out or None


def webp_durations(data):
    """Trvanie snímkov animovaného WebP v ms; [] ak je WebP platné, ale nie je animované; None, ak to WebP nie je."""
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    pos, animated, out = 12, False, []
    while pos + 8 <= len(data):
        tag = data[pos:pos + 4]
        size = struct.unpack_from("<I", data, pos + 4)[0]
        body = pos + 8
        if tag == b"VP8X" and size >= 1:
            animated = bool(data[body] & 0x02)
        elif tag == b"ANMF" and size >= 16 and body + 15 <= len(data):
            out.append(int.from_bytes(data[body + 12:body + 15], "little") or DEFAULT_DELAY_MS)
        pos = body + size + (size & 1)
    return out if animated else []


def sniff(data):
    """gif | webp | None (ostatné formáty sa berú ako nehybný obrázok)."""
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _time(ms):
    value = GLib.TimeVal()
    value.tv_sec = int(ms) // 1000
    value.tv_usec = int(ms % 1000 * 1000)
    return value


class FileScene(Scene):
    """Prehráva snímky súboru v slučke. animated je pravdivé, kým sa nevie, že súbor je nehybný alebo pokazený.

    threaded=False načíta hneď a v tom istom vlákne (testy, nástroje bez hlavnej slučky).
    """
    fps = MAX_FPS

    def __init__(self, path, speed=1.0, budget=BUDGET_BYTES, threaded=True):
        self.path = path
        self.speed = speed
        self.budget = budget
        self.threaded = threaded
        self.animated = True
        self.loading = False            # snímky sa práve načítavajú (kým nie sú, kreslí sa podklad)
        self.problem = ""               # prečo sa súbor nedá zobraziť (celý), alebo v čom je upravený
        self.info = ""                  # čo sa načítalo, pre Nastavenia
        self.memory = 0                 # bajtov v pamäti
        self._size = None               # rozmer plátna poslednej požiadavky
        self._generation = 0
        self._frames = []
        self._step_ms = 100.0
        self._loop_ms = 0.0

    # ---------- načítanie ----------
    def load(self, width, height):
        """Zaistí snímky pre plátno width x height: opakované volanie s rovnakým rozmerom nič nerobí."""
        if self._size == (width, height):
            return
        self._size = (width, height)
        self._generation += 1
        generation = self._generation
        self.loading = True
        if not self.threaded:
            self._finish(generation, self._prepare(width, height))
            return

        def work():
            result = self._prepare(width, height)
            GLib.idle_add(self._finish, generation, result)
        threading.Thread(target=work, name="filescene-load", daemon=True).start()

    def _finish(self, generation, result):
        """Hlavné vlákno: prevezme výsledok, ak medzitým neprišla novšia požiadavka."""
        if generation != self._generation:
            return False
        self.loading = False
        for name, value in result.items():
            setattr(self, name, value)
        return False

    def _prepare(self, width, height):
        """Načíta súbor; nesiaha na stav scény (beží aj vo vlákne) a vráti atribúty, ktoré sa majú nastaviť."""
        result = {"_frames": [], "problem": "", "info": "", "memory": 0, "animated": False,
                  "_step_ms": 100.0, "_loop_ms": 0.0, "fps": MAX_FPS}
        try:
            self._read(width, height, result)
        except (OSError, GLib.Error) as err:
            result.update(_frames=[], animated=False, info="", memory=0,
                          problem="%s: %s" % (os.path.basename(self.path) or self.path,
                                              getattr(err, "message", None) or getattr(err, "strerror", None) or err))
        return result

    def _read(self, width, height, result):
        if os.path.getsize(self.path) > MAX_FILE_BYTES:
            result["problem"] = "Súbor je príliš veľký (najviac %d MB)." % (MAX_FILE_BYTES // 1048576)
            return
        with open(self.path, "rb") as f:
            data = f.read()
        kind = sniff(data)
        durations = gif_durations(data) if kind == "gif" else webp_durations(data) if kind == "webp" else None
        animation = GdkPixbuf.PixbufAnimation.new_from_file(self.path)
        half = ((width + 1) // 2, (height + 1) // 2)
        per_frame = half[0] * half[1] * 4
        if animation.is_static_image() or not durations or len(durations) < 2 or sum(durations) <= 0:
            if kind == "webp" and durations and len(durations) > 1:
                result["problem"] = "Animované WebP sa v tomto systéme nedá prehrať, ukáže sa prvý snímok."
            result.update(_frames=[self._surface(animation.get_static_image(), half)], memory=per_frame,
                          info="nehybný obrázok, %s" % _megabytes(per_frame))
            return
        total = float(sum(durations))
        fps, count = float(MAX_FPS), math.ceil(total * MAX_FPS / 1000)
        most = max(1, self.budget // per_frame)
        if count > most:
            fps = most * 1000.0 / total
            if fps < MIN_FPS:
                fps, count = float(MIN_FPS), most
                result["problem"] = ("Animácia trvá %.1f s a nezmestí sa do pamäte (najviac %s): použije sa len jej "
                                     "začiatok, %.1f s." % (total / 1000, _megabytes(self.budget), most / MIN_FPS))
            else:
                count = most
        step = 1000.0 / fps
        iterator = animation.get_iter(_time(0))
        frames = []
        for k in range(count):
            iterator.advance(_time((k + 0.5) * step))
            frames.append(self._surface(iterator.get_pixbuf(), half))
        loop = count * step if result["problem"] else total
        result.update(_frames=frames, _step_ms=step, _loop_ms=loop, animated=True, fps=min(MAX_FPS, max(1, round(fps))),
                      memory=per_frame * len(frames),
                      info="%s, %.1f s, %s" % (frames_text(len(frames)), loop / 1000, _megabytes(per_frame * len(frames))))

    @staticmethod
    def _surface(pixbuf, size):
        """Snímok zväčšený tak, aby vyplnil size (cover), vystredený, ako cairo povrch."""
        w, h = size
        pw, ph = max(1, pixbuf.get_width()), max(1, pixbuf.get_height())
        scale = max(w / pw, h / ph)
        sw, sh = max(w, math.ceil(pw * scale)), max(h, math.ceil(ph * scale))
        scaled = pixbuf.scale_simple(sw, sh, GdkPixbuf.InterpType.BILINEAR)
        cropped = scaled.new_subpixbuf((sw - w) // 2, (sh - h) // 2, w, h)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        cr = cairo.Context(surface)
        cr.set_source_rgb(*BACKGROUND)
        cr.paint()
        Gdk.cairo_set_source_pixbuf(cr, cropped, 0, 0)
        cr.paint()
        surface.flush()
        return surface

    # ---------- kreslenie ----------
    def render(self, cr, width, height, t):
        self.load(width, height)
        if not self._frames:
            cr.set_source_rgb(*BACKGROUND)
            cr.paint()
            return
        index = 0
        if len(self._frames) > 1 and self._loop_ms > 0:
            position = (t * self.speed * 1000.0) % self._loop_ms
            index = min(int(position / self._step_ms), len(self._frames) - 1)
        frame = self._frames[index]
        cr.save()
        cr.scale(width / frame.get_width(), height / frame.get_height())
        cr.set_source_surface(frame, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        cr.paint()
        cr.restore()


def frames_text(count):
    """„1 snímka“, „3 snímky“, „40 snímok“."""
    if count == 1:
        return "1 snímka"
    return "%d %s" % (count, "snímky" if 2 <= count % 100 <= 4 or (count % 10 in (2, 3, 4) and not 11 <= count % 100 <= 14)
                      else "snímok")


def _megabytes(size):
    return "%.1f MB" % (size / 1048576)
