"""Stránka Hardvér › Obrazovky: rozlíšenie, frekvencia, mierka a otočenie zistených monitorov.

Monitory a ich režimy hlási kompozitor (latte_common/outputs.py), tu sa len ponúkajú a použijú.
Zmena sa najprv vyskúša a používateľ ju musí do 15 s potvrdiť, inak sa sama vráti: zlé rozlíšenie
môže nechať čiernu obrazovku a bez návratu by sa dala opraviť len z konzoly. Potvrdená voľba sa uloží
(displays.toml) a použije sa pri každom prihlásení.
"""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib  # noqa: E402

from latte_common import displays, outputs  # noqa: E402
from latte_settings import pages  # noqa: E402

CONFIRM_SECONDS = 15
MISSING_TITLE = "Zatiaľ chýba"


def dropdown(labels, on_change):
    drop = Gtk.DropDown.new_from_strings(labels)
    drop.connect("notify::selected", lambda w, _p: on_change(w.get_selected()))
    return drop


def option_row(title, note, control):
    row = Gtk.Box(spacing=16)
    row.add_css_class("settings-row")
    text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
    text.set_valign(Gtk.Align.CENTER)
    text.append(pages.label(title, "row-title"))
    if note:
        text.append(pages.label(note, "row-note"))
    row.append(text)
    control.set_valign(Gtk.Align.CENTER)
    row.append(control)
    return row


class MonitorBlock:
    """Jeden monitor: výber režimu, ktorý sa použije až tlačidlom Použiť."""

    def __init__(self, view, ident, head):
        self.view = view
        self.ident = ident
        self.head = head
        self.updating = False
        width, height, refresh, scale, transform = displays.current_state(head)
        self.want = {"width": width, "height": height, "refresh": refresh, "scale": scale, "transform": transform}

        self.resolutions = displays.resolutions(head)
        if (width, height) not in self.resolutions and width:
            self.resolutions.insert(0, (width, height))
        self.rates = []
        self.scales = sorted(set(displays.SCALES) | {round(scale, 3)})
        self.transforms = list(displays.TRANSFORMS)
        if self.want["transform"] not in self.transforms:
            self.transforms.append(self.want["transform"])

        recommended = displays.recommended_resolution(head)
        res_labels = [displays.format_resolution(w, h) + (" (odporúčané)" if (w, h) == recommended else "")
                      for w, h in self.resolutions]
        self.res_drop = dropdown(res_labels or ["neznáme"], self.on_resolution)
        self.rate_drop = dropdown(["neznáma"], self.on_rate)
        suggested = displays.recommended_scale(head)
        self.scale_drop = dropdown([displays.format_scale(s) + (" (odporúčané)" if abs(s - suggested) < 1e-6 else "")
                                    for s in self.scales], self.on_scale)
        self.transform_drop = dropdown([displays.TRANSFORM_LABELS.get(t, t) for t in self.transforms], self.on_transform)

        self.error = pages.label("", "row-error")
        self.error.set_visible(False)
        self.apply_button = Gtk.Button(label="Použiť")
        self.apply_button.add_css_class("suggested-action")
        self.apply_button.connect("clicked", lambda _b: self.apply())
        self.recommend_button = Gtk.Button(label="Odporúčané nastavenie")
        self.recommend_button.connect("clicked", lambda _b: self.use_recommended())
        self.revert_button = Gtk.Button(label="Zahodiť výber")
        self.revert_button.connect("clicked", lambda _b: self.reset_choice())

        self.widget = self.build()
        self.sync_widgets()

    # ---------- skladanie ----------
    def build(self):
        head = self.head
        size = displays.diagonal_inches(head)
        subtitle = " · ".join(x for x in (head.name, "%.0f″" % size if size else "", displays.summary(head)) if x)
        top = Gtk.Box(spacing=12)
        icon = Gtk.Image.new_from_icon_name("video-display-symbolic")
        icon.set_pixel_size(28)
        top.append(icon)
        names = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
        names.append(pages.label(displays.title(head), "row-title"))
        names.append(pages.label(subtitle, "row-note"))
        top.append(names)
        if not head.enabled:
            top.append(pages.label("vypnutý", "row-note"))

        rows = [
            option_row("Rozlíšenie", "", self.res_drop),
            option_row("Obnovovacia frekvencia", "", self.rate_drop),
            option_row("Mierka", "Väčšie písmo a ovládacie prvky na veľmi ostrých monitoroch.", self.scale_drop),
            option_row("Orientácia", "", self.transform_drop),
        ]
        buttons = Gtk.Box(spacing=8)
        buttons.set_margin_top(10)
        buttons.append(self.apply_button)
        buttons.append(self.recommend_button)
        buttons.append(self.revert_button)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.add_css_class("monitor-block")
        top.add_css_class("monitor-head")
        box.append(top)
        box.append(pages.settings_group(rows))
        box.append(self.error)
        box.append(buttons)
        return box

    # ---------- výber ----------
    def sync_widgets(self):
        """Prvky ukážu aktuálny výber (self.want); zmena prvku sa nepovažuje za voľbu používateľa."""
        self.updating = True
        try:
            w, h = self.want["width"], self.want["height"]
            if (w, h) in self.resolutions:
                self.res_drop.set_selected(self.resolutions.index((w, h)))
            self.rates = displays.rates(self.head, w, h) or [self.want["refresh"]]
            if self.want["refresh"] not in self.rates:
                self.rates.append(self.want["refresh"])
            self.rate_drop.set_model(Gtk.StringList.new([displays.format_rate(r) for r in self.rates]))
            self.rate_drop.set_selected(self.rates.index(self.want["refresh"]))
            self.rate_drop.set_sensitive(len(self.rates) > 1)
            self.res_drop.set_sensitive(len(self.resolutions) > 1)
            scale = round(self.want["scale"], 3)
            if scale in self.scales:
                self.scale_drop.set_selected(self.scales.index(scale))
            self.transform_drop.set_selected(self.transforms.index(self.want["transform"]))
        finally:
            self.updating = False
        current = displays.current_state(self.head)
        pending = self.state() != current
        self.apply_button.set_sensitive(pending and not self.view.window.confirm_pending())
        self.revert_button.set_sensitive(pending)

    def state(self):
        w = self.want
        return (w["width"], w["height"], w["refresh"], w["scale"], w["transform"])

    def on_resolution(self, index):
        if self.updating or index >= len(self.resolutions):
            return
        width, height = self.resolutions[index]
        self.want.update(width=width, height=height,
                         refresh=displays.pick_rate(self.head, width, height, self.want["refresh"]))
        self.sync_widgets()

    def on_rate(self, index):
        if not self.updating and index < len(self.rates):
            self.want["refresh"] = self.rates[index]
            self.sync_widgets()

    def on_scale(self, index):
        if not self.updating and index < len(self.scales):
            self.want["scale"] = self.scales[index]
            self.sync_widgets()

    def on_transform(self, index):
        if not self.updating and index < len(self.transforms):
            self.want["transform"] = self.transforms[index]
            self.sync_widgets()

    def use_recommended(self):
        resolution = displays.recommended_resolution(self.head)
        if resolution:
            width, height = resolution
            self.want.update(width=width, height=height, refresh=displays.recommended_rate(self.head, width, height))
        self.want.update(scale=displays.recommended_scale(self.head), transform="normal")
        self.sync_widgets()

    def reset_choice(self):
        width, height, refresh, scale, transform = displays.current_state(self.head)
        self.want.update(width=width, height=height, refresh=refresh, scale=scale, transform=transform)
        self.show_error("")
        self.sync_widgets()

    def show_error(self, text):
        self.error.set_text(text)
        self.error.set_visible(bool(text))

    def flash(self):
        self.widget.add_css_class("flash")
        GLib.timeout_add(1600, lambda: (self.widget.remove_css_class("flash"), False)[1])

    # ---------- použitie ----------
    def apply(self):
        window = self.view.window
        if window.confirm_pending():
            window.notify("Najprv potvrď alebo vráť predchádzajúcu zmenu obrazovky.")
            return
        before = displays.current_state(self.head)
        after = self.state()
        change = displays.change_for(self.head, *after)
        if not change:
            return
        try:
            error = outputs.apply({self.head.name: change})
        except outputs.OutputsError as err:
            error = str(err)
        if error:
            self.show_error("Zmenu sa nepodarilo použiť: %s" % error)
            return
        self.show_error("")
        name = displays.title(self.head)
        window.ask_keep(
            "%s: %s." % (name, displays.format_resolution(after[0], after[1])
                         + (" · " + displays.format_rate(after[2]) if after[2] else "")
                         + " · " + displays.format_scale(after[3])),
            CONFIRM_SECONDS,
            on_keep=lambda: self.keep(after),
            on_revert=lambda: self.revert(before))

    def keep(self, state):
        try:
            displays.save_monitor(self.ident, *state)
        except OSError as err:
            self.view.window.notify("Voľba sa nepodarila uložiť, po novom prihlásení sa nepoužije: %s" % (err.strerror or err))
        self.view.rebuild()

    def revert(self, state):
        try:
            with outputs.Client() as client:
                head = next(h for h in client.monitors() if h.name == self.head.name)
                error = client.apply({head.name: displays.change_for(head, *state)})
        except (outputs.OutputsError, StopIteration) as err:
            error = str(err) or "monitor zmizol"
        if error:
            self.view.window.notify("Návrat na pôvodné nastavenie sa nepodaril: %s" % error)
        self.view.rebuild()


class DisplayView(pages.View):
    def __init__(self, window, page, obj=""):
        self.window = window
        self.page = page
        self.target = obj
        self.blocks = {}
        self.widget = Gtk.Box(hexpand=True, vexpand=True)
        self.rebuild()

    def rebuild(self):
        child = self.widget.get_first_child()
        if child is not None:
            self.widget.remove(child)
        self.blocks = {}
        blocks = []
        try:
            heads = outputs.read()
        except outputs.OutputsError as err:
            heads = []
            blocks.append(pages.notice("Monitory sa nepodarilo zistiť: %s." % err, danger=True))
        found = displays.identify(heads)
        for ident, head in sorted(found.items(), key=lambda kv: kv[1].id):
            block = MonitorBlock(self, ident, head)
            self.blocks[head.name] = block
            blocks.append(block.widget)
        if heads and self.target and self.target not in self.blocks:
            blocks.insert(0, pages.notice("Monitor %s teraz nie je zapojený." % self.target))
        if not heads and not blocks:
            blocks.append(pages.notice("Nenašiel sa žiadny monitor."))
        if heads:
            note = pages.label(
                "Zmenu ti ukážem hneď a do %d s ju potvrdíš, inak sa vráti. Potvrdená voľba sa uloží k monitoru "
                "(%s) a použije sa pri každom prihlásení." % (CONFIRM_SECONDS, pages.short_path(displays.config_path())),
                "row-note")
            note.set_margin_top(16)
            blocks.append(note)
        again = Gtk.Button(label="Znova zistiť monitory", halign=Gtk.Align.START)
        again.set_margin_top(10)
        again.connect("clicked", lambda _b: self.rebuild())
        blocks.append(again)
        blocks.append(pages.group_title(MISSING_TITLE))
        blocks.append(pages.settings_group([pages.label("•  " + item, "settings-row") for item in self.page.contents]))
        scroll, _body = pages.scrolled_page(self.page.title, self.page.description, *blocks)
        self.widget.append(scroll)
        if self.target in self.blocks:
            GLib.idle_add(self.blocks[self.target].flash)

    def focus_key(self, key_id):
        pass
