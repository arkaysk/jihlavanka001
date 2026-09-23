"""Textúra rohových dlaždíc lišty (docs/lista-a-rohy.md, časť 3).

BarTexture drží jedno plátno a jednu scénu. Scénu kreslí raz za snímku do spoločného povrchu;
TextureView (widget) z neho len kopíruje svoj výsek. Päta L v lište a kmeň L v popupe sú dva
povrchy Waylandu, ale kreslia z toho istého povrchu, takže sú vo fáze a bez švu.

Súradnice plátna: počiatok v rohu obrazovky, x doprava, y nahor. Výsek je (x, y, šírka, výška).

Nastavenia (appearance.toml, oddiel bars) sa zbierajú do Config; build z nej vyrobí plátna.
"""
import sys
from dataclasses import dataclass

import cairo
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Graphene", "1.0")
from gi.repository import Gtk, GLib, Graphene  # noqa: E402

from latte_common import scenes  # noqa: E402
from latte_shell import geometry  # noqa: E402

MOTIONS = ("always", "hover", "off")
DEFAULT_LEFT, DEFAULT_RIGHT = "scene:matrix", "scene:gears"
TILES = (("apps", "bars.left", False), ("resources", "bars.right", True))     # druh dlaždice, kľúč, pravá?


class BarTexture:
    """Jedno plátno L. dim: stlmenie textúry pod textom (0 až 0.9), zapečené do plátna. motion: kedy sa hýbe
    (always | hover: len pod kurzorom alebo kým je otvorený popup | off: statický snímok)."""

    def __init__(self, scene, width=geometry.TEXTURE_WIDTH, height=None, right=False, dim=0.6, motion="always",
                 name="", report=None):
        self.scene = scene
        self.name = name                    # kľúč nastavenia (bars.left), do hlásení
        self.report = report or (lambda text: print("latte-shell:", text, file=sys.stderr))
        self.reported = ""
        self.right = right
        self.dim = dim
        self.motion = motion
        self.hovered = False
        self.width = width
        self.height = height if height is not None else geometry.texture_height()
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        self.views = []
        self.source = 0
        self.started = GLib.get_monotonic_time()
        self.settings = Gtk.Settings.get_default()
        if self.settings is not None:
            self.settings.connect("notify::gtk-enable-animations", lambda *_a: self.sync())

    # ---------- pohľady ----------
    def view(self, rect, right=False, awake=False):
        """Widget, ktorý ukazuje výsek plátna. right: pohľad je pri pravom okraji obrazovky.

        rect je výsek alebo funkcia, ktorá ho vráti (výsek závisí od výšky lišty, ktorá sa môže zmeniť).
        awake: kým je pohľad zobrazený, plátno sa hýbe aj v režime „len pod kurzorom“ (kmeň otvoreného popupu).
        """
        return TextureView(self, rect, right, awake)

    def set_hovered(self, flag):
        """Kurzor je nad dlaždicou (režim „len pod kurzorom“)."""
        if flag != self.hovered:
            self.hovered = flag
            self.sync()

    def set_bar_height(self):
        """Výška lišty sa zmenila: plátno je iné, pohľady majú nové výseky."""
        self.height = geometry.texture_height()
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        self.sync()

    def add_view(self, view):
        if view not in self.views:
            self.views.append(view)
        self.sync()

    def remove_view(self, view):
        if view in self.views:
            self.views.remove(view)
        self.sync()

    def pixel_rect(self, rect):
        """Výsek plátna (y nahor) ako obdĺžnik povrchu (y nadol)."""
        x, y, w, h = rect
        return x, self.height - y - h, w, h

    # ---------- čas a kreslenie ----------
    def moving(self):
        enabled = self.settings is None or self.settings.get_property("gtk-enable-animations")
        if not (self.views and self.scene.animated and enabled) or self.motion == "off":
            return False
        if self.motion == "hover":
            return self.hovered or any(view.awake for view in self.views)
        return True

    def sync(self):
        """Časovač beží, len kým je niečo viditeľné, scéna sa hýbe a pohyb nie je vypnutý."""
        running = self.moving()
        if running and not self.source:
            self.source = GLib.timeout_add(max(1000 // self.scene.fps, 20), self.tick)
        elif not running and self.source:
            GLib.source_remove(self.source)
            self.source = 0
        if self.views:
            self.render(scenes.STILL_TIME if not running else self.elapsed())

    def elapsed(self):
        return (GLib.get_monotonic_time() - self.started) / 1e6

    def tick(self):
        if not self.moving():
            self.source = 0
            self.sync()                     # statický snímok (napr. nehybný obrázok, ktorý sa práve načítal)
            return False
        self.render(self.elapsed())
        return True

    def render(self, t):
        """Nakreslí len tú časť plátna, ktorú niektorý pohľad ukazuje."""
        cr = cairo.Context(self.surface)
        for view in self.views:
            px, py, pw, ph = self.pixel_rect(view.rect)
            cr.rectangle(px, py, pw, ph)
        cr.clip()
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        self.scene.render(cr, self.width, self.height, t)
        scenes.dim_overlay(cr, self.width, self.height, geometry.bar_height(), geometry.corner_width(),
                           self.dim, self.right)
        self.surface.flush()
        problem = getattr(self.scene, "problem", "")            # napr. súbor sa nedá načítať: ohlási sa raz
        if problem != self.reported:
            self.reported = problem
            if problem:
                self.report("%s: %s" % (self.name, problem))
        for view in self.views:
            view.queue_draw()


class TextureView(Gtk.Widget):
    """Výsek plátna. Nemá vlastnú minimálnu veľkosť: dostane, čo mu pridelí rodič (okraj tlačidla
    by inak zväčšil lištu o pixel). Kreslí sa zarovnaný k spodnému a vonkajšiemu okraju obrazovky,
    takže prípadné orezanie padne na hornú hranu, nie na riadok pri okraji."""

    __gtype_name__ = "LatteTextureView"

    def __init__(self, texture, rect, right=False, awake=False):
        super().__init__()
        self.texture = texture
        self.rect_source = rect
        self.right = right
        self.awake = awake
        self.connect("map", lambda _w: texture.add_view(self))
        self.connect("unmap", lambda _w: texture.remove_view(self))

    @property
    def rect(self):
        return self.rect_source() if callable(self.rect_source) else self.rect_source

    def do_measure(self, _orientation, _for_size):
        return 0, 0, -1, -1

    def do_snapshot(self, snapshot):
        width, height = self.get_width(), self.get_height()
        cr = snapshot.append_cairo(Graphene.Rect().init(0, 0, width, height))
        px, py, pw, ph = self.texture.pixel_rect(self.rect)
        cr.set_source_surface(self.texture.surface, (width - pw if self.right else 0) - px, height - ph - py)
        cr.rectangle(0, 0, width, height)
        cr.fill()


def corner_rect(right):
    """Výsek plátna, ktorý ukazuje päta L (rohová dlaždica). Pravá dlaždica je pri pravom okraji plátna."""
    width = geometry.corner_width()
    return (geometry.TEXTURE_WIDTH - width if right else 0, 0, width, geometry.bar_height())


def trunk_rect():
    """Výsek plátna, ktorý ukazuje kmeň L: pás nad lištou."""
    return (0, geometry.bar_height(), geometry.POPUP_WIDTH, geometry.ARM_HEIGHT)


@dataclass(frozen=True)
class Config:
    """Všetko, od čoho závisí vzhľad textúr (nastavenia oddielu bars a farby motívu). Rovnaká Config = nič sa
    nemení, takže sa plátna nestavajú znova pri každej zmene súboru s nastaveniami."""
    left: str = DEFAULT_LEFT
    right: str = DEFAULT_RIGHT
    motion: str = "always"
    speed: float = 1.0
    dim: float = 0.6
    palette: scenes.Palette = scenes.DEFAULT_PALETTE

    @classmethod
    def from_values(cls, values, palette=scenes.DEFAULT_PALETTE, report=None):
        """Config z hodnôt domény appearance (Store.values()). Neznámy zápis zdroja sa nahradí predvoleným a
        ohlási sa (report), bez tichej degradácie."""
        report = report or (lambda text: print("latte-shell:", text, file=sys.stderr))

        def source(key, default):
            spec = values.get(key, default)
            if scenes.is_known(spec):
                return spec
            report("%s: neznámy zdroj %r, použije sa %s" % (key, spec, default))
            return default

        motion = values.get("bars.motion", "always")
        return cls(left=source("bars.left", DEFAULT_LEFT), right=source("bars.right", DEFAULT_RIGHT),
                   motion=motion if motion in MOTIONS else "always",
                   speed=float(values.get("bars.speed", 1.0)), dim=float(values.get("bars.dim", 0.6)), palette=palette)


def build(config=None):
    """Plátna podľa Config: {druh dlaždice: BarTexture}. Obyčajná dlaždica (solid:motív) plátno nemá."""
    config = config or Config()
    textures = {}
    for kind, key, right in TILES:
        scene = scenes.parse(getattr(config, "right" if right else "left"), config.speed, config.palette, right)
        if scene is not None:
            textures[kind] = BarTexture(scene, right=right, dim=config.dim, motion=config.motion, name=key)
    return textures
