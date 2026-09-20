"""Scény: textúry kreslené kódom (docs/lista-a-rohy.md, časť 4).

Scéna nezná okno ani GTK: dostane cairo kontext, rozmer plátna a čas v sekundách a nakreslí obraz.
Obraz je čistá funkcia času (žiadny stav medzi snímkami), takže dva pohľady na to isté plátno dajú
ten istý obraz, statický snímok pri vypnutom pohybe je len obraz v pevnom čase a scény sa dajú testovať.
Scéna má kresliť len do orezanej oblasti kontextu (`cr.clip_extents()`): kto potrebuje kúsok plátna,
nezaplatí za celé.

Zápis zdroja v nastaveniach: `solid:#RRGGBB` alebo `scene:matrix` (parse).
"""
import random
import re

import cairo

STILL_TIME = 7.0                # v tomto čase sa scéna ukáže, keď je pohyb vypnutý

_HEX = re.compile(r"^#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$")


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


def parse(spec, speed=1.0):
    """Scéna zo zápisu zdroja, alebo None, ak zápis nepoznáme (volajúci použije náhradnú)."""
    kind, _sep, value = (spec or "").partition(":")
    if kind == "solid":
        found = _HEX.match(value)
        if found:
            return Solid(tuple(int(part, 16) / 255 for part in found.groups()))
    elif kind == "scene" and value == "matrix":
        return Matrix(speed)
    return None
