"""Textúra rohových dlaždíc lišty (docs/lista-a-rohy.md, časť 3).

BarTexture drží jedno plátno a jednu scénu. Scénu kreslí raz za snímku do spoločného povrchu;
TextureView (widget) z neho len kopíruje svoj výsek. Päta L v lište a kmeň L v popupe sú dva
povrchy Waylandu, ale kreslia z toho istého povrchu, takže sú vo fáze a bez švu.

Súradnice plátna: počiatok v rohu obrazovky, x doprava, y nahor. Výsek je (x, y, šírka, výška).
"""
import cairo
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Graphene", "1.0")
from gi.repository import Gtk, GLib, Graphene  # noqa: E402

from latte_common import scenes  # noqa: E402
from latte_shell.geometry import (BAR_HEIGHT, CORNER_WIDTH, TEXTURE_HEIGHT,  # noqa: E402
                                  TEXTURE_WIDTH)

# Zdroje textúry podľa dlaždice; None = obyčajná dlaždica z motívu. V R4 to nahradia nastavenia.
DEFAULT_SOURCES = {"apps": "scene:matrix", "resources": None}


class BarTexture:
    def __init__(self, scene, width=TEXTURE_WIDTH, height=TEXTURE_HEIGHT):
        self.scene = scene
        self.width = width
        self.height = height
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.views = []
        self.source = 0
        self.started = GLib.get_monotonic_time()
        self.settings = Gtk.Settings.get_default()
        if self.settings is not None:
            self.settings.connect("notify::gtk-enable-animations", lambda *_a: self.sync())

    # ---------- pohľady ----------
    def view(self, rect, right=False):
        """Widget, ktorý ukazuje výsek plátna. right: pohľad je pri pravom okraji obrazovky."""
        return TextureView(self, rect, right)

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
        return bool(self.views) and self.scene.animated and enabled

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
        self.surface.flush()
        for view in self.views:
            view.queue_draw()


class TextureView(Gtk.Widget):
    __gtype_name__ = "LatteTextureView"

    """Výsek plátna. Nemá vlastnú minimálnu veľkosť: dostane, čo mu pridelí rodič (okraj tlačidla
    by inak zväčšil lištu o pixel). Kreslí sa zarovnaný k spodnému a vonkajšiemu okraju obrazovky,
    takže prípadné orezanie padne na hornú hranu, nie na riadok pri okraji."""

    def __init__(self, texture, rect, right=False):
        super().__init__()
        self.texture = texture
        self.rect = rect
        self.right = right
        self.connect("map", lambda _w: texture.add_view(self))
        self.connect("unmap", lambda _w: texture.remove_view(self))

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
    return (TEXTURE_WIDTH - CORNER_WIDTH if right else 0, 0, CORNER_WIDTH, BAR_HEIGHT)


def build(sources=None):
    """Plátna podľa zdrojov: {druh dlaždice: BarTexture}; zápis, ktorý nepoznáme, dá obyčajnú dlaždicu."""
    textures = {}
    for kind, spec in (sources or DEFAULT_SOURCES).items():
        scene = scenes.parse(spec)
        if scene is not None:
            textures[kind] = BarTexture(scene)
    return textures
