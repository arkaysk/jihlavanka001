"""Ovládacie prvky Nastavení skladané zo schémy: jeden riadok na kľúč (docs/nastavenia.md).

Riadok nepozná význam kľúča, len jeho typ. Zapisuje výhradne cez Store.set/reset, takže overenie
hodnoty, vrstvy (správca prekrýva používateľa) a atomický zápis sú tie isté ako všade. Neplatná
hodnota alebo zlyhaný zápis sa ukáže pod riadkom, nikdy sa nepohltí potichu.
"""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

from latte_common import appearance  # noqa: E402
from latte_common.settings import SettingsError  # noqa: E402

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
        if key.type == "bool":
            return self.bool_control()
        if key.type == "enum":
            return self.choice_control(list(key.choices), [key.choice_label(c) for c in key.choices])
        if key.type in ("int", "float"):
            return self.number_control()
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
