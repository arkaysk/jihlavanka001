"""Scény: textúry kreslené kódom (docs/lista-a-rohy.md, časť 4).

Scéna nezná okno ani GTK: dostane cairo kontext, rozmer plátna a čas v sekundách a nakreslí obraz.
Obraz je čistá funkcia času (žiadny stav medzi snímkami), takže dva pohľady na to isté plátno dajú
ten istý obraz, statický snímok pri vypnutom pohybe je len obraz v pevnom čase a scény sa dajú testovať.
Scéna má kresliť len do orezanej oblasti kontextu (`cr.clip_extents()`): kto potrebuje kúsok plátna,
nezaplatí za celé.

Zápis zdroja v nastaveniach (parse, CHOICES): `solid:motív` (obyčajná dlaždica z motívu, bez textúry),
`solid:#RRGGBB`, `scene:matrix`, `scene:gears`, `scene:glow`, `file:/absolútna/cesta` (filescene.py: GIF, animované
WebP, obrázok). Ďalší druh je ďalšia vetva v parse.
"""
import math
import random
import re
from typing import NamedTuple

import cairo

STILL_TIME = 7.0                # v tomto čase sa scéna ukáže, keď je pohyb vypnutý

_HEX = re.compile(r"^#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$")

PLAIN = "solid:motív"           # dlaždica bez textúry, farba z motívu (CSS)
# zdroje, ktoré Nastavenia ponúkajú (zápis, názov); iné zápisy (solid:#RRGGBB) sú platné, len sa neponúkajú
CHOICES = (
    (PLAIN, "Jedna farba (podľa motívu)"),
    ("scene:matrix", "Matrix: stekajúci kód"),
    ("scene:gears", "Ozubené prevody"),
    ("scene:glow", "Pomalé svetlo"),
)


class Palette(NamedTuple):
    """Farby motívu, ktoré scény smú použiť (RGB 0 až 1)."""
    accent: tuple
    fg: tuple


DEFAULT_PALETTE = Palette(accent=(0.85, 0.57, 0.23), fg=(0.95, 0.92, 0.88))


def palette_from_colors(colors):
    """Paleta scén z farieb motívu (tokens.colors: rola -> #RRGGBB); čo chýba alebo je pokazené, dá predvolené."""
    def rgb(role, fallback):
        try:
            return tuple(int(colors[role][i:i + 2], 16) / 255 for i in (1, 3, 5))
        except (KeyError, ValueError, TypeError, IndexError):
            return fallback
    return Palette(accent=rgb("accent", DEFAULT_PALETTE.accent), fg=rgb("fg", DEFAULT_PALETTE.fg))


def mix(a, b, amount):
    return tuple(x + (y - x) * amount for x, y in zip(a, b))


class Scene:
    fps = 10                    # koľkokrát za sekundu sa má prekresliť
    animated = True             # False: stačí nakresliť raz

    def render(self, cr, width, height, t):
        raise NotImplementedError


class Solid(Scene):
    """Jedna farba."""
    fps = 0
    animated = False

    def __init__(self, rgb):
        self.rgb = rgb

    def render(self, cr, width, height, t):
        cr.set_source_rgb(*self.rgb)
        cr.paint()


class Matrix(Scene):
    """Stekajúci kód: stĺpce znakov, v každom svetlá hlava a doznievajúci chvost.

    Pokojný pohyb (stĺpec preskočí jeden riadok za 0,5 až 1 s), znaky sa menia pomaly a v každom
    stĺpci inak. Farby: klasická zelená na tmavom podklade.
    """
    CHARS = "0123456789$+-*/<>=:;|ZTXCAEHK"
    CELL_W = 11
    CELL_H = 14
    FONT_SIZE = 12
    BACKGROUND = (0.043, 0.071, 0.047)
    TAIL = (0.22, 0.92, 0.42)
    HEAD = (0.86, 1.0, 0.90)
    SPEED = (1.0, 2.2)              # riadkov za sekundu
    LENGTH = (6, 15)                # dĺžka chvosta v riadkoch
    GAP = (1, 7)                    # prázdne riadky, kým stĺpec začne znova
    CHANGE_SECONDS = 2.0            # ako často sa mení znak v jednej bunke

    def __init__(self, speed=1.0):
        self.speed = speed
        self._columns = {}

    def _column(self, index):
        """Vlastnosti stĺpca; závisia len od jeho čísla, takže sa nemenia medzi snímkami."""
        found = self._columns.get(index)
        if found is None:
            rng = random.Random(index * 7919 + 13)
            found = (rng.uniform(*self.SPEED), rng.randint(*self.LENGTH),
                     rng.randint(*self.GAP), rng.random())
            self._columns[index] = found
        return found

    def render(self, cr, width, height, t):
        cr.set_source_rgb(*self.BACKGROUND)
        cr.paint()
        x1, y1, x2, y2 = cr.clip_extents()
        rows = height // self.CELL_H + 1
        cr.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(self.FONT_SIZE)

        first_col = max(int(x1 // self.CELL_W), 0)
        last_col = min(int(x2 // self.CELL_W), width // self.CELL_W)
        first_row = max(int(y1 // self.CELL_H), 0)
        last_row = min(int(y2 // self.CELL_H), rows - 1)
        for col in range(first_col, last_col + 1):
            speed, length, gap, phase = self._column(col)
            cycle = rows + length + gap
            head = (t * speed * self.speed + phase * cycle) % cycle
            for row in range(max(first_row, int(head - length) + 1), min(last_row, int(head)) + 1):
                fade = 1.0 - (head - row) / length
                if fade <= 0:
                    continue
                r, g, b = self.HEAD if head - row < 1 else self.TAIL
                cr.set_source_rgba(r, g, b, min(1.0, fade * fade * 1.1))
                step = int(t / self.CHANGE_SECONDS + phase * 5 + col * 0.37)
                char = self.CHARS[(col * 73856093 ^ row * 19349663 ^ step * 83492791) % len(self.CHARS)]
                cr.move_to(col * self.CELL_W, (row + 1) * self.CELL_H - 3)
                cr.show_text(char)


class Gear(NamedTuple):
    n: int                      # počet zubov
    r: float                    # rozstupový polomer
    x: float
    y: float
    parent: int                 # index kolesa, do ktorého zaberá (-1: hnacie)
    alpha: float                # smer od rodiča k tomuto kolesu


class Gears(Scene):
    """Ozubené prevody: sústava do seba zaberajúcich kolies, ktorá rastie z rohu plátna a otáča sa pomaly.

    Rozloženie je pevne dané (semienko), takže je rovnaké pri každom vykreslení a nezávisí od času. Uhly kolies
    sú funkcia času: hnacie koleso sa točí rovnomerne a každé ďalšie sa otáča opačne a v pomere zubov, s fázou,
    pri ktorej zub zapadá do medzery (gears() a angles() sa dajú testovať bez kreslenia). Pravý roh je zrkadlo.
    """
    fps = 10
    MODULE = 5.0                    # veľkosť zuba: rozstupový polomer = MODULE * počet zubov / 2
    TEETH = (8, 10, 12, 14, 16, 18)
    BACKGROUND = (0.055, 0.047, 0.04)
    SPEED = 0.30                    # radiány za sekundu hnacieho kolesa
    DEAD_X = 240.0                  # vpravo od tejto x a pod DEAD_Y · výška plátna nie je L vidieť (pod ramenom)
    DEAD_Y = 0.5

    def __init__(self, speed=1.0, palette=DEFAULT_PALETTE, right=False):
        self.speed = speed
        self.palette = palette
        self.right = right
        self._layouts = {}

    def gears(self, width, height):
        """Kolesá plátna: hnacie pri ľavom dolnom rohu a z neho sa rozrastá sústava (BFS, pevné semienko)."""
        key = (width, height)
        if key not in self._layouts:
            self._layouts[key] = self._grow(width, height)
        return self._layouts[key]

    def _grow(self, width, height):
        rng = random.Random(7)
        m = self.MODULE
        first = Gear(14, m * 14 / 2, 58.0, height - 42.0, -1, 0.0)
        gears = [first]
        queue = [0]
        target = max(6, int(width / 34))
        tries = 0
        while queue and len(gears) < target and tries < 1500:
            parent = queue.pop()            # od najnovšieho: sústava sa tiahne ďalej, nezhlukuje sa pri rohu
            p = gears[parent]
            for _child in range(2):
                for _attempt in range(12):
                    tries += 1
                    n = rng.choice(self.TEETH)
                    r = m * n / 2
                    alpha = math.radians(max(-100.0, min(80.0, rng.gauss(-4.0, 42.0))))
                    x = p.x + (p.r + r) * math.cos(alpha)
                    y = p.y + (p.r + r) * math.sin(alpha)
                    if not (-0.3 * r <= x <= width + 0.3 * r and -0.5 * r <= y <= height + 0.5 * r):
                        continue
                    if x > self.DEAD_X and y > self.DEAD_Y * height:
                        continue            # výsek L pod ramenom, kam nie je vidieť
                    if any(g is not p and math.hypot(g.x - x, g.y - y) < g.r + r + 2.0 * m for g in gears):
                        continue
                    gears.append(Gear(n, r, x, y, parent, alpha))
                    queue.append(len(gears) - 1)
                    break
        return gears

    def angles(self, gears, t):
        """Uhly všetkých kolies v čase t. Dieťa zaberá do rodiča: jeho zub zapadne do medzery rodiča."""
        out = []
        for g in gears:
            if g.parent < 0:
                out.append(self.SPEED * self.speed * t)
            else:
                p = gears[g.parent]
                out.append(g.alpha + math.pi - math.pi / g.n + (g.alpha - out[g.parent]) * p.n / g.n)
        return out

    def render(self, cr, width, height, t):
        cr.set_source_rgb(*self.BACKGROUND)
        cr.paint()
        cr.save()                           # zrkadlenie pravého rohu nesmie zostať platné pre toho, kto kreslí ďalej
        if self.right:
            cr.translate(width, 0)
            cr.scale(-1, 1)
        x1, y1, x2, y2 = cr.clip_extents()
        gears = self.gears(width, height)
        angles = self.angles(gears, t)
        m = self.MODULE
        ar, ag, ab = self.palette.accent
        for i, (g, theta) in enumerate(zip(gears, angles)):
            tip = g.r + 0.9 * m
            if g.x + tip < x1 or g.x - tip > x2 or g.y + tip < y1 or g.y - tip > y2:
                continue
            root, pitch = g.r - 1.15 * m, 2 * math.pi / g.n
            cr.save()
            cr.translate(g.x, g.y)
            for k in range(g.n):
                a = theta + k * pitch
                if k == 0:
                    cr.move_to(root * math.cos(a - 0.30 * pitch), root * math.sin(a - 0.30 * pitch))
                cr.line_to(tip * math.cos(a - 0.16 * pitch), tip * math.sin(a - 0.16 * pitch))
                cr.line_to(tip * math.cos(a + 0.16 * pitch), tip * math.sin(a + 0.16 * pitch))
                cr.line_to(root * math.cos(a + 0.30 * pitch), root * math.sin(a + 0.30 * pitch))
                cr.arc(0, 0, root, a + 0.30 * pitch, a + 0.70 * pitch)
            cr.close_path()
            cr.new_sub_path()
            cr.arc(0, 0, g.r * 0.26, 0, 2 * math.pi)
            cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            cr.set_source_rgba(ar, ag, ab, 0.38 + 0.10 * (i % 3))
            cr.fill_preserve()
            cr.set_source_rgba(min(1, ar + 0.15), min(1, ag + 0.15), min(1, ab + 0.15), 0.75)
            cr.set_line_width(1.0)
            cr.stroke()
            cr.restore()
        cr.restore()


class Glow(Scene):
    """Pomalé svetlo: mäkké farebné škvrny plynúce po dlhých dráhach (jedna perióda 40 až 120 s)."""
    fps = 8
    BACKGROUND = (0.07, 0.052, 0.04)
    BLOBS = 6

    def __init__(self, speed=1.0, palette=DEFAULT_PALETTE):
        self.speed = speed
        rng = random.Random(3)
        warm = (0.85, 0.36, 0.22)
        colors = [palette.accent, palette.fg, mix(palette.accent, warm, 0.5),
                  palette.accent, mix(palette.fg, palette.accent, 0.5), warm]
        self.blobs = []
        for i in range(self.BLOBS):
            self.blobs.append((rng.uniform(0.05, 0.16), rng.uniform(0.04, 0.13), rng.uniform(0, 2 * math.pi),
                               rng.uniform(0, 2 * math.pi), rng.uniform(110, 210), colors[i], rng.uniform(0.40, 0.62)))

    def center(self, blob, width, height, t):
        ax, ay, px, py = blob[:4]
        return (width * (0.5 + 0.5 * math.sin(ax * t * self.speed + px)),
                height * (0.5 + 0.5 * math.sin(ay * t * self.speed + py)))

    def render(self, cr, width, height, t):
        cr.set_source_rgb(*self.BACKGROUND)
        cr.paint()
        x1, y1, x2, y2 = cr.clip_extents()
        for blob in self.blobs:
            radius, (r, g, b), alpha = blob[4], blob[5], blob[6]
            cx, cy = self.center(blob, width, height, t)
            if cx + radius < x1 or cx - radius > x2 or cy + radius < y1 or cy - radius > y2:
                continue
            glow = cairo.RadialGradient(cx, cy, 0, cx, cy, radius)
            glow.add_color_stop_rgba(0, r, g, b, alpha)
            glow.add_color_stop_rgba(1, r, g, b, 0)
            cr.set_source(glow)
            cr.arc(cx, cy, radius, 0, 2 * math.pi)
            cr.fill()


def dim_overlay(cr, width, height, bar_height, foot_width, dim, right=False):
    """Tmavý prechod nad textúrou L, aby zostal čitateľný text na kmeni a popis dlaždice.

    Plátno: hore kmeň (výška height - bar_height), dole päta (bar_height, široká foot_width, pri ľavom alebo
    pravom okraji). Kmeň je pri päte slabšie stmavený a pod textom silnejšie, päta silnejšie dole (popis).
    dim je 0 (nič) až 0.9; kreslí len do orezanej oblasti kontextu.
    """
    if dim <= 0:
        return
    weak, strong = dim * 0.5, min(0.95, dim + 0.22)
    arm = height - bar_height
    color = (0.016, 0.04, 0.024)

    if right:
        edge, far = width - foot_width, width - foot_width - 132
    else:
        edge, far = foot_width, foot_width + 132
    trunk = cairo.LinearGradient(edge, 0, far, 0)
    trunk.add_color_stop_rgba(0, *color, weak)
    trunk.add_color_stop_rgba(1, *color, strong)
    cr.rectangle(0, 0, width, arm)
    cr.set_source(trunk)
    cr.fill()

    foot = cairo.LinearGradient(0, arm, 0, height)
    foot.add_color_stop_rgba(0, *color, max(0.0, weak - 0.05))
    foot.add_color_stop_rgba(1, *color, min(0.98, strong + 0.03))
    cr.rectangle(width - foot_width if right else 0, arm, foot_width, bar_height)
    cr.set_source(foot)
    cr.fill()


def parse(spec, speed=1.0, palette=None, right=False):
    """Scéna zo zápisu zdroja, alebo None: buď je to obyčajná dlaždica (PLAIN), alebo zápis nepoznáme
    (is_known to rozlíši; volajúci v oboch prípadoch nekreslí textúru). Súbor sa tu nečíta: FileScene ho načíta
    pri prvom kreslení a chybu ohlási v `problem`."""
    palette = palette or DEFAULT_PALETTE
    kind, _sep, value = (spec or "").partition(":")
    if kind == "solid":
        found = _HEX.match(value)
        if found:
            return Solid(tuple(int(part, 16) / 255 for part in found.groups()))
    elif kind == "file":
        if value.startswith("/") and len(value) > 1:
            from latte_common import filescene          # až tu: kódované scény nepotrebujú GdkPixbuf
            return filescene.FileScene(value, speed)
    elif kind == "scene":
        if value == "matrix":
            return Matrix(speed)
        if value == "gears":
            return Gears(speed, palette, right)
        if value == "glow":
            return Glow(speed, palette)
    return None


def custom_label(spec):
    """Názov zdroja mimo ponuky (CHOICES) pre Nastavenia: „Súbor: a.gif“, „Farba: #102030“; inak zápis s poznámkou."""
    kind, _sep, value = (spec or "").partition(":")
    if kind == "file" and value.startswith("/"):
        return "Súbor: %s" % (value.rstrip("/").rsplit("/", 1)[-1] or value)
    if kind == "solid" and _HEX.match(value):
        return "Farba: %s" % value.upper()
    return "%s (neznámy zdroj)" % (spec or "prázdny")


def source_list(value):
    """(zápisy, názvy, index) pre rozbaľovací zoznam zdrojov: ponuka CHOICES a, ak je value mimo nej (súbor, farba,
    neznámy zápis), ešte jedna „vlastná“ položka na konci. index je položka, ktorá zodpovedá value."""
    specs = [spec for spec, _label in CHOICES]
    labels = [label for _spec, label in CHOICES]
    if value not in specs:
        specs.append(value)
        labels.append(custom_label(value))
    return specs, labels, specs.index(value)


def pick_source(specs, index, current):
    """Zdroj, ktorý sa má zapísať po výbere položky index zo zoznamu specs; None, ak sa nemá zapísať nič: položka je
    mimo zoznamu, alebo je to už aktuálna hodnota.

    GTK doručuje oznámenie o zmene výberu aj vtedy, keď výber nastavil program (a niekedy až neskôr, keď už
    neplatí ochrana pred vlastnými zmenami). Obsluha výberu preto musí byť idempotentná, inak sa
    zápis → obnova → nastavenie zoznamu → oznámenie → zápis točí donekonečna.
    """
    if not 0 <= index < len(specs) or specs[index] == current:
        return None
    return specs[index]


def is_known(spec):
    """Zápis zdroja, ktorý parse pozná (vrátane obyčajnej dlaždice)."""
    return spec == PLAIN or parse(spec) is not None
