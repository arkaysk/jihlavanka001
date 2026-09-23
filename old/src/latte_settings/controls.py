"""Ovládacie prvky Nastavení skladané zo schémy: jeden riadok na kľúč (docs/nastavenia.md).

Riadok nepozná význam kľúča, len jeho typ. Zapisuje výhradne cez Store.set/reset, takže overenie
hodnoty, vrstvy (správca prekrýva používateľa) a atomický zápis sú tie isté ako všade. Neplatná
hodnota alebo zlyhaný zápis sa ukáže pod riadkom, nikdy sa nepohltí potichu.
"""
import cairo
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk, Gio, GLib  # noqa: E402

from latte_common import appearance, scenes  # noqa: E402
from latte_shell import geometry  # noqa: E402       # len rozmery lišty (čisté konštanty a orezanie)
from latte_common.settings import SettingsError  # noqa: E402

SLIDER_THROTTLE_MS = 100         # ako často sa zapíše hodnota, kým sa ťahá posuvník

APPLY_NOTE = {
    "session": "Prejaví sa po novom prihlásení.",
    "restart": "Prejaví sa po reštarte komponentu.",
}
LOCKED_NOTE = "Túto hodnotu určil správca systému, nedá sa zmeniť."
FLASH_MS = 1600


def note_label(css):
    label = Gtk.Label(xalign=0, wrap=True)
    label.add_css_class(css)
    label.set_visible(False)
    return label


class KeyRow(Gtk.Box):
    """Riadok „názov, popis a ovládací prvok“ pre jeden kľúč schémy."""

    def __init__(self, store, key):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.add_css_class("settings-row")
        self.store = store
        self.key = key
        self.updating = False           # zmena prvku zo Store nie je zmena od používateľa
        self.focus_widget = None
        self.choices = []

        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
        text.set_valign(Gtk.Align.CENTER)
        title = Gtk.Label(label=key.label, xalign=0, wrap=True)
        title.add_css_class("row-title")
        text.append(title)
        if key.description:
            desc = Gtk.Label(label=key.description, xalign=0, wrap=True)
            desc.add_css_class("row-note")
            text.append(desc)
        self.note = note_label("row-note")
        text.append(self.note)
        self.error = note_label("row-error")
        text.append(self.error)
        self.append(text)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        controls.set_valign(Gtk.Align.CENTER)
        self.control = self.build_control()
        controls.append(self.control)
        self.reset_button = Gtk.Button(icon_name="edit-undo-symbolic")
        self.reset_button.add_css_class("flat")
        self.reset_button.set_tooltip_text("Vrátiť predvolenú hodnotu")
        self.reset_button.connect("clicked", lambda _b: self.commit_reset())
        controls.append(self.reset_button)
        self.append(controls)
        self.refresh()

    # ---------- prvky podľa typu ----------
    def build_control(self):
        key = self.key
        if key.id == "theme.id":
            return self.theme_control()
        if key.id in ("bars.left", "bars.right"):
            return self.source_control()
        if key.type == "bool":
            return self.bool_control()
        if key.type == "enum":
            return self.choice_control(list(key.choices), [key.choice_label(c) for c in key.choices])
        if key.type in ("int", "float"):
            return self.slider_control() if key.control == "slider" else self.number_control()
        if key.type == "color":
            return self.color_control()
        return self.text_control(chooser=key.type == "path")

    def bool_control(self):
        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.connect("notify::active", lambda w, _p: self.commit(w.get_active()))
        self.set_widget = lambda v: switch.set_active(bool(v))
        self.focus_widget = switch
        return switch

    def choice_control(self, values, labels):
        """Rozbaľovací výber; hodnota mimo zoznamu (napr. zmazaný motív) sa doplní, aby ostala vidieť."""
        self.choices = list(values)
        self.labels = list(labels)
        drop = Gtk.DropDown.new_from_strings(self.labels)
        drop.connect("notify::selected", lambda w, _p: self.commit(self.choices[w.get_selected()])
                     if w.get_selected() < len(self.choices) else None)

        def set_widget(value):
            if value not in self.choices:
                self.choices.append(value)
                self.labels.append("%s (nenájdený)" % value)
                drop.set_model(Gtk.StringList.new(self.labels))
            drop.set_selected(self.choices.index(value))

        self.set_widget = set_widget
        self.focus_widget = drop
        return drop

    def theme_control(self):
        themes, _problems = appearance.list_themes()
        return self.choice_control([t.id for t in themes], [t.name for t in themes])

    def number_control(self):
        key = self.key
        is_int = key.type == "int"
        step = key.step or 1
        low = key.minimum if key.minimum is not None else -1e9
        high = key.maximum if key.maximum is not None else 1e9
        adjustment = Gtk.Adjustment(lower=low, upper=high, step_increment=step, page_increment=step * 5)
        digits = 0 if is_int else (2 if step < 0.1 else 1)
        spin = Gtk.SpinButton(adjustment=adjustment, digits=digits)
        spin.set_numeric(True)
        spin.connect("value-changed", lambda w: self.commit(
            w.get_value_as_int() if is_int else round(w.get_value(), 3)))
        self.set_widget = lambda v: spin.set_value(v)
        self.focus_widget = spin
        if not key.unit:
            return spin
        box = Gtk.Box(spacing=6)
        box.append(spin)
        unit = Gtk.Label(label=key.unit)
        unit.add_css_class("row-note")
        box.append(unit)
        return box

    def source_control(self):
        """Výber zdroja textúry rohovej dlaždice, tlačidlá na vlastný súbor a farbu a pod tým živý náhľad L.

        Náhľad kreslí rovnaký kód ako lišta (latte_common/scenes.py) s rýchlosťou, stlmením a pohybom z ostatných
        riadkov stránky, takže ich zmena je hneď vidieť. Zápis mimo ponuky (súbor, farba) sa doplní do zoznamu
        ako „Súbor: názov“ alebo „Farba: #RRGGBB“, aby ostal vidieť. Pod náhľadom je stav: čo sa načítalo
        (snímky, dĺžka, pamäť), alebo prečo súbor nejde.
        """
        self.choices, self.labels, _index = scenes.source_list(scenes.PLAIN)
        drop = Gtk.DropDown.new_from_strings(self.labels)

        def picked(widget, _pspec):
            # idempotentné: oznámenie o výbere, ktorý nastavil program (nie používateľ), nič nezapíše
            spec = scenes.pick_source(self.choices, widget.get_selected(), self.store.get(self.key.id))
            if spec is not None:
                self.commit(spec)

        drop.connect("notify::selected", picked)

        status = Gtk.Label(xalign=0, wrap=True, max_width_chars=44)
        status.add_css_class("row-note")
        status.set_visible(False)

        def show_status(text, problem):
            status.set_text(text)
            status.set_visible(bool(text))
            for css, on in (("row-error", problem), ("row-note", not problem)):
                if on:
                    status.add_css_class(css)
                else:
                    status.remove_css_class(css)

        preview = LPreview(self.store, right=self.key.id == "bars.right", on_status=show_status)

        pick_file = Gtk.Button(label="Súbor…")
        pick_file.set_tooltip_text("Vlastná animácia (GIF, WebP) alebo obrázok")
        pick_file.connect("clicked", lambda _b: self.choose_file())
        color = Gtk.ColorDialogButton(dialog=Gtk.ColorDialog(with_alpha=False))
        start = Gdk.RGBA()
        start.red, start.green, start.blue, start.alpha = (*scenes.Matrix.BACKGROUND, 1.0)     # kým nie je zvolená žiadna
        color.set_rgba(start)
        color.set_tooltip_text("Jedna farba (tmavá, lebo text na nej je svetlý)")

        def color_changed(widget, _pspec):
            spec = "solid:" + self.hex_of(widget.get_rgba())
            if not self.updating and spec.upper() != str(self.store.get(self.key.id)).upper():
                self.commit(spec)

        color.connect("notify::rgba", color_changed)
        row = Gtk.Box(spacing=8)
        row.append(drop)
        row.append(pick_file)
        row.append(color)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.append(row)
        box.append(preview)
        box.append(status)

        shown = {"labels": None, "spec": None}

        def set_widget(value):
            """Zobrazí hodnotu. Zoznam a náhľad sa menia len keď treba: vymeniť model pri každom obnovení by
            spustilo oznámenie o výbere, to by zapísalo a obnovilo znova, a tak donekonečna."""
            self.choices, self.labels, index = scenes.source_list(value)
            if self.labels != shown["labels"]:
                shown["labels"] = list(self.labels)
                drop.set_model(Gtk.StringList.new(self.labels))
            if drop.get_selected() != index:
                drop.set_selected(index)
            if value.startswith("solid:#"):
                rgba = Gdk.RGBA()
                if rgba.parse(value[6:]) and self.hex_of(color.get_rgba()) != self.hex_of(rgba):
                    color.set_rgba(rgba)
            if value != shown["spec"]:
                shown["spec"] = value
                preview.set_spec(value)

        self.set_widget = set_widget
        self.focus_widget = drop
        return box

    def choose_file(self):
        """Dialóg na výber animácie alebo obrázka; výsledok sa zapíše ako file:/cesta."""
        dialog = Gtk.FileDialog(title="Animácia alebo obrázok pre roh lišty")
        images = Gtk.FileFilter(name="Animácie a obrázky (GIF, WebP, PNG, JPEG)")
        for mime in ("image/gif", "image/webp", "image/png", "image/jpeg"):
            images.add_mime_type(mime)
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(images)
        dialog.set_filters(filters)

        def done(dlg, result):
            try:
                chosen = dlg.open_finish(result)
            except GLib.Error:
                return                                          # zrušené
            if chosen is not None and chosen.get_path():
                self.commit("file:" + chosen.get_path())

        dialog.open(self.get_root(), None, done)

    def slider_control(self):
        """Posuvník s hodnotou: zmena sa zapisuje priebežne (najviac raz za SLIDER_THROTTLE_MS), takže sa
        počas ťahania hneď prejaví (napr. výška lišty), a zapíše sa vždy aj posledná hodnota."""
        key = self.key
        is_int = key.type == "int"
        step = key.step or 1
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, key.minimum, key.maximum, step)
        scale.set_size_request(260, -1)
        scale.set_draw_value(True)
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        scale.set_digits(0 if is_int else (2 if step < 0.1 else 1))
        unit = (" " + key.unit) if key.unit else ""
        scale.set_format_value_func(lambda _s, v: ("%d" % round(v) if is_int else "%g" % round(v, 3)) + unit)
        pending = {"timer": 0}

        def fire():
            pending["timer"] = 0
            value = scale.get_value()
            self.commit(int(round(value)) if is_int else round(value, 3))
            return False

        def moved(_scale):
            if not self.updating and not pending["timer"]:
                pending["timer"] = GLib.timeout_add(SLIDER_THROTTLE_MS, fire)

        scale.connect("value-changed", moved)
        self.set_widget = lambda v: scale.set_value(v)
        self.focus_widget = scale
        return scale

    def color_control(self):
        button = Gtk.ColorDialogButton(dialog=Gtk.ColorDialog(with_alpha=False))
        button.connect("notify::rgba", lambda w, _p: self.commit(self.hex_of(w.get_rgba())))
        hint = Gtk.Label(label="podľa motívu")
        hint.add_css_class("row-note")
        box = Gtk.Box(spacing=8)
        box.append(hint)
        box.append(button)

        def set_widget(value):
            hint.set_visible(value == "")
            # prázdne = farba motívu: vzorka ukáže tú, ktorú skutočne uvidí, nie náhodnú
            shown = value or appearance.current_tokens().colors.get("accent", "")
            rgba = Gdk.RGBA()
            if shown and rgba.parse(shown):
                button.set_rgba(rgba)

        self.set_widget = set_widget
        self.focus_widget = button
        return box

    @staticmethod
    def hex_of(rgba):
        return "#%02X%02X%02X" % tuple(round(max(0.0, min(1.0, c)) * 255) for c in (rgba.red, rgba.green, rgba.blue))

    def text_control(self, chooser):
        entry = Gtk.Entry(width_chars=26, placeholder_text="(predvolené)" if self.key.allow_empty else "")
        entry.connect("activate", lambda w: self.commit(w.get_text().strip()))
        leave = Gtk.EventControllerFocus()
        leave.connect("leave", lambda _c: self.commit(entry.get_text().strip()))
        entry.add_controller(leave)
        self.set_widget = lambda v: entry.set_text(str(v))
        self.focus_widget = entry
        if not chooser:
            return entry
        box = Gtk.Box(spacing=6)
        box.append(entry)
        pick = Gtk.Button(label="Vybrať…")
        pick.connect("clicked", lambda _b: self.choose_file(entry))
        box.append(pick)
        return box

    def choose_file(self, entry):
        dialog = Gtk.FileDialog(title=self.key.label)

        def done(dlg, result):
            try:
                file = dlg.open_finish(result)
            except GLib.Error:
                return                  # zrušené
            if file is not None and file.get_path():
                entry.set_text(file.get_path())
                self.commit(file.get_path())

        dialog.open(self.get_root(), None, done)

    # ---------- zápis a obnova ----------
    def commit(self, value):
        if self.updating:
            return
        key = self.key
        try:
            if key.allow_empty and value == "":
                if self.store.source(key.id) == "user":
                    self.store.reset(key.id)
            elif value != self.store.get(key.id):
                self.store.set(key.id, value)
        except SettingsError as err:
            self.show_error(str(err))
        except OSError as err:
            self.show_error("Zápis do %s zlyhal: %s" % (self.store.path, err.strerror or err))
        else:
            self.show_error("")
        self.refresh()

    def commit_reset(self):
        try:
            self.store.reset(self.key.id)
        except (SettingsError, OSError) as err:
            self.show_error(str(err))
        else:
            self.show_error("")
        self.refresh()

    def show_error(self, text):
        self.error.set_text(text)
        self.error.set_visible(bool(text))

    def refresh(self):
        """Prvok ukáže hodnotu, ktorú má Store (po zápise, po zmene súboru mimo Nastavení)."""
        key = self.key
        locked = self.store.locked(key.id)
        self.updating = True
        try:
            self.set_widget(self.store.get(key.id))
        finally:
            self.updating = False
        self.control.set_sensitive(not locked)
        self.reset_button.set_visible(self.store.source(key.id) == "user" and not locked)
        note = LOCKED_NOTE if locked else APPLY_NOTE.get(key.apply, "")
        self.note.set_text(note)
        self.note.set_visible(bool(note))

    def flash(self):
        """Krátko zvýrazní riadok a dá mu fokus (skok z výsledkov hľadania)."""
        self.add_css_class("flash")
        GLib.timeout_add(FLASH_MS, lambda: (self.remove_css_class("flash"), False)[1])
        if self.focus_widget is not None:
            self.focus_widget.grab_focus()


class LPreview(Gtk.DrawingArea):
    """Živý náhľad tvaru L (kmeň nad pätou) so zdrojom textúry; beží, len kým je viditeľný.

    Tvar a rozmery sú z geometrie lišty (výška z nastavení), kreslenie je scenes.parse + scenes.dim_overlay,
    teda presne to, čo robí lišta. Hýbe sa, len kým je nad ním kurzor a WAKE_SECONDS po zmene nastavenia
    (zdroj, rýchlosť, stlmenie, pohyb); inak ukáže statický snímok. Softvérové vykresľovanie totiž pri každom
    obraze prekreslí celé okno: dva stále bežiace náhľady stáli 35 % jadra.
    """
    SCALE = 0.36
    FPS = 10
    WAKE_SECONDS = 4.0

    def __init__(self, store, right, on_status=None):
        super().__init__()
        self.store = store
        self.right = right
        self.on_status = on_status or (lambda _text, _problem: None)
        self.status = None
        self.was_loading = False
        self.hovered = False
        self.awake_until = 0.0
        self.settings_seen = None
        self.scene = None
        self.spec = ""
        self.started = GLib.get_monotonic_time()
        self.source = 0
        self.surface = None
        self.set_content_width(int(geometry.TEXTURE_WIDTH * self.SCALE))
        self.set_content_height(int((geometry.MAX_BAR_HEIGHT + geometry.ARM_HEIGHT) * self.SCALE))
        self.set_halign(Gtk.Align.END)
        self.set_draw_func(self.draw)
        self.connect("map", lambda _w: self.start())
        self.connect("unmap", lambda _w: self.stop())
        hover = Gtk.EventControllerMotion()
        hover.connect("enter", lambda *_a: setattr(self, "hovered", True))
        hover.connect("leave", lambda *_a: setattr(self, "hovered", False))
        self.add_controller(hover)

    def wake(self):
        """Náhľad sa na chvíľu rozhýbe (zmenilo sa niečo, čo chce používateľ vidieť)."""
        self.awake_until = GLib.get_monotonic_time() / 1e6 + self.WAKE_SECONDS

    def watched_settings(self):
        return tuple(self.store.get(key) for key in ("bars.speed", "bars.dim", "bars.motion"))

    def bar_height(self):
        return geometry.clamp_bar_height(self.store.get("bar.height"))

    def set_spec(self, spec):
        """Zdroj sa zmenil (alebo sa zmenili farby, rýchlosť): nová scéna."""
        self.spec = spec
        palette = scenes.palette_from_colors(appearance.current_tokens(self.store).colors)
        self.scene = scenes.parse(spec, self.store.get("bars.speed"), palette, self.right)
        self.status = None
        self.wake()
        self.paint()
        self.queue_draw()

    def start(self):
        if not self.source:
            self.source = GLib.timeout_add(1000 // self.FPS, self.tick)
        self.paint()

    def stop(self):
        if self.source:
            GLib.source_remove(self.source)
            self.source = 0

    def tick(self):
        scene = self.scene
        if scene is None:
            return True
        loading = getattr(scene, "loading", False)
        seen = self.watched_settings()
        if seen != self.settings_seen:
            if self.settings_seen is not None:
                self.wake()
            self.settings_seen = seen
        active = self.hovered or GLib.get_monotonic_time() / 1e6 < self.awake_until
        moving = scene.animated and active and self.store.get("bars.motion") != "off"
        if moving or loading or self.was_loading:               # aj raz po načítaní súboru
            if scene.speed != self.store.get("bars.speed"):
                scene.speed = self.store.get("bars.speed")
            self.paint()
            self.queue_draw()
        self.was_loading = loading
        return True

    def paint(self):
        """Nakreslí L do plátna v skutočnej veľkosti; draw ho len zmenší."""
        width, bar = geometry.TEXTURE_WIDTH, self.bar_height()
        arm = geometry.ARM_HEIGHT
        foot = 2 * bar
        height = bar + arm
        if self.surface is None or self.surface.get_height() != height:
            self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(self.surface)
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.rectangle(0, 0, width, arm)                                          # kmeň
        cr.rectangle(width - foot if self.right else 0, arm, foot, bar)         # päta
        cr.clip()
        if self.scene is None:                                                  # obyčajná dlaždica bez textúry
            cr.set_source_rgba(0.5, 0.5, 0.5, 0.18)
            cr.paint()
        else:
            still = self.store.get("bars.motion") == "off"
            self.scene.render(cr, width, height, scenes.STILL_TIME if still else (GLib.get_monotonic_time() - self.started) / 1e6)
            scenes.dim_overlay(cr, width, height, bar, foot, self.store.get("bars.dim"), self.right)
        self.surface.flush()
        self.report_status()

    def report_status(self):
        """Stav zdroja pod náhľadom: čo sa načítalo, alebo prečo súbor nejde (len keď sa zmenil)."""
        scene = self.scene
        if scene is None:
            status = ("", False)
        elif getattr(scene, "loading", False):
            status = ("Načítava sa…", False)
        elif getattr(scene, "problem", ""):
            status = (scene.problem, True)
        else:
            status = (getattr(scene, "info", ""), False)
        if status != self.status:
            self.status = status
            self.on_status(*status)

    def draw(self, _area, cr, width, height):
        if self.surface is None:
            return
        scale = self.SCALE
        cr.translate(width - self.surface.get_width() * scale if self.right else 0, height - self.surface.get_height() * scale)
        cr.scale(scale, scale)
        cr.set_source_surface(self.surface, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR)
        cr.paint()
