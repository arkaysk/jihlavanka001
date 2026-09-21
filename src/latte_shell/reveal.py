"""Otváranie a zatváranie popupu L (docs/lista-a-rohy.md, časť 3, bod 4).

Kmeň L sa vysunie z hornej hrany päty: jeho výška a šírka narastajú naraz (od šírky päty), potom sa
nad ním objaví panel s obsahom. Zatváranie je opačne. Matematika je čistá (reveal_rect, phases),
Reveal je widget, ktorý dieťa len orezáva (rozloženie sa nemení), Tween ho poháňa hodinami okna.
"""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Graphene", "1.0")
from gi.repository import Gtk, Graphene  # noqa: E402

OPEN_MS = 380
CLOSE_MS = 300
ARM_SHARE = 0.75                # kmeň sa odhalí v prvých troch štvrtinách času
PANEL_FROM = 0.5                # panel sa začne objavovať v polovici času


def ease_out(x):
    """Rýchly štart a mäkký dobeh."""
    x = min(max(x, 0.0), 1.0)
    return 1.0 - (1.0 - x) ** 3


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3.0 - 2.0 * x)


def phases(p):
    """Postup animácie p (0 zatvorené, 1 otvorené) na (odhalenie kmeňa, priehľadnosť panelu)."""
    return ease_out(p / ARM_SHARE), smooth((p - PANEL_FROM) / (1.0 - PANEL_FROM))


def reveal_rect(progress, width, height, start_width, right=False):
    """Odhalená časť kmeňa (x, y, šírka, výška): rastie od päty, ktorá je pri spodnom a vonkajšom okraji."""
    w = start_width + (width - start_width) * progress
    h = height * progress
    return (width - w if right else 0.0), height - h, w, h


class Reveal(Gtk.Widget):
    """Zobrazí dieťa orezané na odhalenú časť; rozloženie dieťaťa sa počas animácie nemení."""
    __gtype_name__ = "LatteReveal"

    def __init__(self, child, start_width, right=False):
        super().__init__()
        self.child = child
        self.start_width = start_width
        self.right = right
        self.progress = 1.0
        child.set_parent(self)

    def set_progress(self, progress):
        self.progress = progress
        self.queue_draw()

    def do_measure(self, orientation, for_size):
        return self.child.measure(orientation, for_size)

    def do_size_allocate(self, width, height, baseline):
        self.child.allocate(width, height, baseline, None)

    def do_snapshot(self, snapshot):
        x, y, w, h = reveal_rect(self.progress, self.get_width(), self.get_height(), self.start_width, self.right)
        snapshot.push_clip(Graphene.Rect().init(x, y, w, h))
        self.snapshot_child(self.child, snapshot)
        snapshot.pop()

    def do_dispose(self):
        if self.child is not None:
            self.child.unparent()
            self.child = None
        Gtk.Widget.do_dispose(self)


class Tween:
    """Plynulý postup 0..1 podľa hodín okna. Prepnutie smeru uprostred pokračuje z aktuálnej hodnoty."""

    def __init__(self, widget, on_update):
        self.widget = widget
        self.on_update = on_update
        self.value = 0.0
        self.tick_id = 0

    def animations_enabled(self):
        settings = Gtk.Settings.get_default()
        return settings is None or settings.get_property("gtk-enable-animations")

    def run(self, target, duration_ms, on_done=None):
        self.stop()
        if not self.animations_enabled() or self.value == target:
            self.value = target
            self.on_update(target)
            if on_done:
                on_done()
            return
        start = self.value
        span = abs(target - start) * duration_ms * 1000.0          # zostávajúca časť času v mikrosekundách
        state = {"t0": None}

        def tick(widget, clock):
            now = clock.get_frame_time()
            if state["t0"] is None:
                state["t0"] = now
            done = min((now - state["t0"]) / span, 1.0) if span > 0 else 1.0
            self.value = start + (target - start) * done
            self.on_update(self.value)
            if done >= 1.0:
                self.tick_id = 0
                if on_done:
                    on_done()
                return False
            return True

        self.tick_id = self.widget.add_tick_callback(tick)

    def stop(self):
        if self.tick_id:
            self.widget.remove_tick_callback(self.tick_id)
            self.tick_id = 0
