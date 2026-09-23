"""Bubliny oznámení (bod 2.7) a karta oznámenia, ktorú používa aj zoznam pod zvončekom."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Pango  # noqa: E402
from gi.repository import Gtk4LayerShell as LayerShell  # noqa: E402

from latte_common import clock  # noqa: E402

TOAST_WIDTH = 380
TEXT_CHARS = 36                 # najviac znakov na riadok, dlhší text sa zalomí
MAX_TOASTS = 5
MARGIN = 12


def icon_for(note):
    """Ikona oznámenia: súbor, názov z témy, ikona aplikácie podľa mena, inak všeobecná."""
    theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
    icon = note.app_icon
    image = Gtk.Image()
    image.set_pixel_size(32)
    if icon.startswith("file://"):
        icon = icon[7:]
    if icon.startswith("/"):
        image.set_from_file(icon)
    elif icon and theme.has_icon(icon):
        image.set_from_icon_name(icon)
    else:
        gicon = None
        for name in (note.app_name, note.app_name.lower()):
            try:
                info = Gio.DesktopAppInfo.new(name + ".desktop") if name else None
            except TypeError:
                info = None
            if info is not None and info.get_icon() is not None:
                gicon = info.get_icon()
                break
        if gicon is not None:
            image.set_from_gicon(gicon)
        else:
            image.set_from_icon_name("dialog-information-symbolic")
    return image


def build_card(note, on_action, on_dismiss, show_time=False):
    """Karta oznámenia. on_action(kľúč) pri tlačidle akcie, on_dismiss() pri ×."""
    card = Gtk.Box(spacing=10)
    card.add_css_class("toast")
    if note.urgency == 2:
        card.add_css_class("critical")
    card.append(icon_for(note))
    icon = card.get_first_child()
    icon.set_valign(Gtk.Align.START)

    text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
    top = Gtk.Box(spacing=6)
    app = Gtk.Label(label=note.app_name or "Oznámenie", xalign=0, hexpand=True)
    app.add_css_class("dim")
    app.set_ellipsize(Pango.EllipsizeMode.END)
    top.append(app)
    if show_time:
        when = Gtk.Label(label=clock.ago(GLib.get_real_time() / 1e6, note.time))
        when.add_css_class("dim")
        top.append(when)
    close = Gtk.Button(icon_name="window-close-symbolic")
    close.add_css_class("flat")
    close.add_css_class("prompt-tool")
    close.set_tooltip_text("Zavrieť")
    close.connect("clicked", lambda _b: on_dismiss())
    top.append(close)
    text.append(top)

    summary = Gtk.Label(label=note.summary, xalign=0, wrap=True)
    summary.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
    summary.set_max_width_chars(TEXT_CHARS)
    summary.add_css_class("toast-summary")
    text.append(summary)
    if note.body:
        body = Gtk.Label(label=note.body, xalign=0, wrap=True)
        body.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        body.set_max_width_chars(TEXT_CHARS)
        body.set_lines(4)
        body.set_ellipsize(Pango.EllipsizeMode.END)
        text.append(body)

    extra = [(key, label) for key, label in note.actions if key != "default"]
    if extra:
        row = Gtk.Box(spacing=6)
        row.set_margin_top(6)
        for key, label in extra:
            button = Gtk.Button(label=label)
            button.add_css_class("toast-action")
            button.connect("clicked", lambda _b, k=key: on_action(k))
            row.append(button)
        text.append(row)
    card.append(text)

    click = Gtk.GestureClick()
    click.connect("released", lambda *_a: on_action("default"))
    card.add_controller(click)
    return card


class ToastStack:
    """Bubliny v pravom hornom rohu. Okno existuje, len kým je nejaká bublina."""

    def __init__(self, app, center):
        self.app = app
        self.center = center
        self.window = None
        self.box = None
        self.cards = {}                 # id -> (karta, zdroj časovača)
        center.on_popup = self.show
        center.on_popup_close = self.hide

    def ensure_window(self):
        if self.window is not None:
            return
        self.window = Gtk.Window(application=self.app)
        self.window.add_css_class("latte-overlay")
        LayerShell.init_for_window(self.window)
        LayerShell.set_layer(self.window, LayerShell.Layer.OVERLAY)
        LayerShell.set_anchor(self.window, LayerShell.Edge.TOP, True)
        LayerShell.set_anchor(self.window, LayerShell.Edge.RIGHT, True)
        LayerShell.set_margin(self.window, LayerShell.Edge.TOP, MARGIN)
        LayerShell.set_margin(self.window, LayerShell.Edge.RIGHT, MARGIN)
        LayerShell.set_exclusive_zone(self.window, -1)
        LayerShell.set_keyboard_mode(self.window, LayerShell.KeyboardMode.NONE)
        LayerShell.set_namespace(self.window, "latte-notifications")
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.box.set_size_request(TOAST_WIDTH, -1)
        self.window.set_child(self.box)
        self.window.present()

    def show(self, note):
        self.hide(note.id, keep_window=True)        # náhrada existujúceho oznámenia
        self.ensure_window()
        card = build_card(
            note,
            lambda key, nid=note.id: self.center.invoke(nid, key) if self.has_action(nid, key)
            else self.center.close(nid),
            lambda nid=note.id: self.center.close(nid),
        )
        source = GLib.timeout_add(note.timeout_ms, self.expire, note.id) if note.timeout_ms else 0
        self.box.prepend(card)
        self.cards[note.id] = (card, source)
        if len(self.cards) > MAX_TOASTS:
            GLib.idle_add(self.expire, next(iter(self.cards)))

    def has_action(self, nid, key):
        note = self.center.find(nid)
        return note is not None and any(k == key for k, _label in note.actions)

    def expire(self, nid):
        entry = self.cards.get(nid)
        if entry is not None:
            self.cards[nid] = (entry[0], 0)             # zdroj časovača sa po False odstráni sám
        self.center.popup_expired(nid)
        return False

    def hide(self, nid, keep_window=False):
        entry = self.cards.pop(nid, None)
        if entry is None:
            return
        card, source = entry
        if source:
            GLib.source_remove(source)
        self.box.remove(card)
        if not self.cards and not keep_window:
            self.window.destroy()
            self.window = self.box = None
