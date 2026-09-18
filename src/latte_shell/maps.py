#!/usr/bin/env python3
"""Popupy LatteOS v tvare L: mapa aplikácií a mapa zdrojov."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gio, GLib  # noqa: E402
from gi.repository import Gtk4LayerShell as LayerShell  # noqa: E402

from latte_common import volumes as vol_mod  # noqa: E402

BAR_HEIGHT = 104
ARM_HEIGHT = 110
MAP_WIDTH = 640
MAP_HEIGHT = 520
MAP_WIDTH_PINNED = 900
MAP_HEIGHT_PINNED = 640
COLUMN = 104


# ---------------------------------------------------------------- obsah
def apps_grid(on_launch):
    flow = Gtk.FlowBox(max_children_per_line=5, selection_mode=Gtk.SelectionMode.NONE)
    flow.set_margin_top(12)
    flow.set_margin_bottom(12)
    flow.set_margin_start(12)
    flow.set_margin_end(12)

    for info in sorted(
        Gio.AppInfo.get_all(), key=lambda a: (a.get_display_name() or "").lower()
    ):
        if not info.should_show():
            continue
        btn = Gtk.Button()
        btn.add_css_class("flat")
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        inner.set_size_request(110, 92)
        icon = Gtk.Image.new_from_gicon(info.get_icon()) if info.get_icon() else Gtk.Image()
        icon.set_pixel_size(40)
        label = Gtk.Label(label=info.get_display_name() or "")
        label.set_wrap(True)
        label.set_max_width_chars(13)
        label.set_justify(Gtk.Justification.CENTER)
        inner.append(icon)
        inner.append(label)
        btn.set_child(inner)
        btn.connect("clicked", lambda _b, i=info: on_launch(i))
        flow.append(btn)

    scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
    scroll.set_child(flow)
    return scroll


def placeholder(text):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True)
    label = Gtk.Label(label=text)
    label.add_css_class("dim")
    label.set_valign(Gtk.Align.CENTER)
    label.set_vexpand(True)
    box.append(label)
    return box


def resources_grid():
    grid = Gtk.FlowBox(max_children_per_line=3, selection_mode=Gtk.SelectionMode.NONE)
    grid.set_margin_top(12)
    grid.set_margin_bottom(12)
    grid.set_margin_start(12)
    grid.set_margin_end(12)

    for v in vol_mod.list_volumes():
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.add_css_class("card-item")
        card.set_size_request(180, 70)
        title = Gtk.Label(label=v.name, xalign=0)
        title.add_css_class("heading")
        note = "systémový zväzok" if v.role == "system" else v.size
        sub = Gtk.Label(label=note, xalign=0)
        sub.add_css_class("dim")
        card.append(title)
        card.append(sub)
        grid.append(card)

    for name, state in [
        ("Kamera", "[STAV]"),
        ("Mikrofón", "[STAV]"),
        ("Tlačiareň", "[STAV]"),
        ("Wi-Fi", "[SIEŤ]"),
    ]:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.add_css_class("card-item")
        card.set_size_request(180, 70)
        title = Gtk.Label(label=name, xalign=0)
        title.add_css_class("heading")
        sub = Gtk.Label(label=state, xalign=0)
        sub.add_css_class("dim")
        card.append(title)
        card.append(sub)
        grid.append(card)

    scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
    scroll.set_child(grid)
    return scroll


# ---------------------------------------------------------------- mapa
class MapPanel(Gtk.Box):
    """Panel s dvoma záložkami a pripináčikom."""

    def __init__(self, kind, on_pin, on_launch, pinned=False):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.kind = kind
        self.on_launch = on_launch
        self.add_css_class("map-panel")
        self.tab = 0

        if kind == "apps":
            titles = ("Nainštalované aplikácie", "Aplikácie bežiace na pozadí")
        else:
            titles = ("Zariadenia", "Siete")

        tabs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        tabs.add_css_class("tabs")
        self.tab_buttons = []
        for i, name in enumerate(titles):
            btn = Gtk.Button(label=name)
            btn.add_css_class("tab")
            btn.set_hexpand(True)
            btn.connect("clicked", lambda _b, idx=i: self.set_tab(idx))
            tabs.append(btn)
            self.tab_buttons.append(btn)

        if not pinned:
            pin = Gtk.Button(icon_name="view-pin-symbolic")
            pin.add_css_class("flat")
            pin.set_tooltip_text("Pripnúť ako okno")
            pin.connect("clicked", lambda _b: on_pin())
            tabs.append(pin)

        self.append(tabs)

        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
        self.append(self.body)
        self.set_tab(0)

    def set_tab(self, idx):
        self.tab = idx
        for i, btn in enumerate(self.tab_buttons):
            if i == idx:
                btn.add_css_class("active")
            else:
                btn.remove_css_class("active")

        child = self.body.get_first_child()
        while child is not None:
            self.body.remove(child)
            child = self.body.get_first_child()

        if self.kind == "apps":
            content = apps_grid(self.on_launch) if idx == 0 else placeholder(
                "[ZOZNAM APLIKÁCIÍ NA POZADÍ]"
            )
        else:
            content = resources_grid() if idx == 0 else placeholder("[SIETE]")
        self.body.append(content)


def arm_box(kind):
    """Vodorovné rameno L so súhrnom."""
    arm = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
    arm.add_css_class("arm")
    arm.set_size_request(-1, ARM_HEIGHT)

    if kind == "apps":
        arm.set_margin_start(COLUMN + 40)
        arm.set_margin_end(20)
        lines = [
            "[POČET] aplikácií · [MIESTO]",
            "App Manager ponúka [POČET] natívnych a [POČET] kontajnerových aplikácií",
            "[POČET] bežiacich procesov",
        ]
    else:
        arm.set_margin_start(20)
        arm.set_margin_end(COLUMN + 40)
        lines = [
            "[POČET] zariadení · [SIEŤ]",
            "Ťahom zariadenia na okno ho pridelíte aplikácii",
            "[STAV HOSTITEĽA]",
        ]

    col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
    col.set_valign(Gtk.Align.CENTER)
    first = Gtk.Label(label=lines[0], xalign=0)
    first.add_css_class("arm-title")
    col.append(first)
    for text in lines[1:]:
        lbl = Gtk.Label(label=text, xalign=0)
        lbl.add_css_class("dim")
        col.append(lbl)
    arm.append(col)
    return arm


def column_box(label_text):
    """Zvislá časť L v rohu obrazovky."""
    col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    col.add_css_class("column")
    col.set_size_request(COLUMN, BAR_HEIGHT)
    lbl = Gtk.Label(label=label_text)
    lbl.add_css_class("corner-label")
    lbl.set_valign(Gtk.Align.END)
    lbl.set_vexpand(True)
    lbl.set_margin_bottom(14)
    col.append(lbl)
    return col


# ---------------------------------------------------------------- popup
class MapOverlay(Gtk.Window):
    """Celoobrazovková vrstva: klik mimo L ju zavrie."""

    def __init__(self, app, kind, on_launch, on_closed):
        super().__init__(application=app)
        self.kind = kind
        self.on_closed = on_closed
        self.add_css_class("latte-overlay")

        LayerShell.init_for_window(self)
        LayerShell.set_layer(self, LayerShell.Layer.OVERLAY)
        for edge in (
            LayerShell.Edge.TOP,
            LayerShell.Edge.BOTTOM,
            LayerShell.Edge.LEFT,
            LayerShell.Edge.RIGHT,
        ):
            LayerShell.set_anchor(self, edge, True)
        LayerShell.set_exclusive_zone(self, -1)
        LayerShell.set_namespace(self, "latte-popup")

        base = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True)
        click = Gtk.GestureClick()
        click.connect("pressed", lambda *_a: self.close_popup())
        base.add_controller(click)

        overlay = Gtk.Overlay()
        overlay.set_child(base)
        self.set_child(overlay)

        shape = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        shape.set_valign(Gtk.Align.END)
        shape.set_halign(Gtk.Align.START if kind == "apps" else Gtk.Align.END)
        shape.set_margin_start(12 if kind == "apps" else 0)
        shape.set_margin_end(0 if kind == "apps" else 12)
        shape.set_margin_bottom(BAR_HEIGHT)

        panel = MapPanel(kind, self.pin, on_launch)
        panel.set_size_request(MAP_WIDTH, MAP_HEIGHT)
        shape.append(panel)

        arm = arm_box(kind)
        arm.set_size_request(MAP_WIDTH, ARM_HEIGHT)
        shape.append(arm)

        overlay.add_overlay(shape)

    def close_popup(self):
        self.on_closed()
        self.destroy()

    def pin(self):
        app = self.get_application()
        win = MapWindow(app, self.kind, getattr(app, "map_window_closed", None))
        if hasattr(app, "register_map_window"):
            app.register_map_window(self.kind, win)
        win.present()
        self.close_popup()


class MapWindow(Gtk.Window):
    """Pripnutá mapa ako bežné okno."""

    def __init__(self, app, kind, on_closed=None):
        super().__init__(application=app)
        self.kind = kind
        self.on_closed = on_closed
        title = "Mapa aplikácií" if kind == "apps" else "Mapa zdrojov"
        self.set_title(title)
        self.set_default_size(MAP_WIDTH_PINNED, MAP_HEIGHT_PINNED)
        panel = MapPanel(kind, lambda: None, self.launch, pinned=True)
        self.set_child(panel)
        self.connect("close-request", self.on_close)

    def on_close(self, *_a):
        if self.on_closed is not None:
            self.on_closed(self.kind)
        return False

    def launch(self, info):
        try:
            info.launch([], None)
        except GLib.Error:
            pass