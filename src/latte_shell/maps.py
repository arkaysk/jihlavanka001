#!/usr/bin/env python3
"""Popupy LatteOS v tvare L: mapa aplikácií a mapa zdrojov."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, Gio, GLib  # noqa: E402
from gi.repository import Gtk4LayerShell as LayerShell  # noqa: E402

from latte_common import hardware  # noqa: E402

BAR_HEIGHT = 104
ARM_HEIGHT = 110
MAP_WIDTH = 640
MAP_HEIGHT = 520
MAP_WIDTH_PINNED = 900
MAP_HEIGHT_PINNED = 640
COLUMN = 104
GROUP_COLUMNS = 2               # skupiny zariadení vedľa seba
TILES_PER_ROW = 3               # dlaždíc v riadku skupiny
GROUP_GAP = 12                  # medzera medzi kartami skupín
GROUP_PADDING = 20              # vodorovná výplň karty skupiny (10 + 10)


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


def pick_icon(names):
    """Prvá ikona zo zoznamu, ktorú téma pozná (vlastné ikony LatteOS sú v data/icons)."""
    theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
    for name in names:
        if theme.has_icon(name):
            return name
    return "computer-symbolic"


def device_tile(item, on_select, on_open):
    """Dlaždica zariadenia: veľká ikona, názov a stav. Klik alebo klepnutie ho vyberie; dvojklik, pravý klik
    a dlhé podržanie ponúknu Nastavenia (hlavná cesta je tlačidlo v ramene L)."""
    tile = Gtk.Button()
    tile.add_css_class("device-tile")
    tile.set_size_request(122, 118)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, halign=Gtk.Align.CENTER)
    holder = Gtk.Box(halign=Gtk.Align.CENTER)
    holder.add_css_class("tile-icon")
    holder.set_size_request(52, 52)
    icon = Gtk.Image.new_from_icon_name(pick_icon(item.icons))
    icon.set_pixel_size(28)
    icon.set_hexpand(True)
    icon.set_vexpand(True)
    holder.append(icon)
    box.append(holder)
    name = Gtk.Label(label=item.name, wrap=True, justify=Gtk.Justification.CENTER, lines=2, ellipsize=3,
                     max_width_chars=15)
    name.add_css_class("tile-name")
    box.append(name)
    note = item.status or item.detail.split(" · ")[0]
    sub = Gtk.Label(label=note, ellipsize=3, max_width_chars=16)
    sub.add_css_class("tile-sub")
    box.append(sub)
    tile.set_child(box)
    tile.set_tooltip_text("%s\n%s" % (item.name, item.detail) if item.detail else item.name)
    tile.connect("clicked", lambda _b: on_select(item))

    popover = Gtk.Popover()
    popover.add_css_class("context-menu")
    popover.set_has_arrow(False)
    settings_button = Gtk.Button()
    settings_button.add_css_class("flat")
    line = Gtk.Box(spacing=10)
    line.append(Gtk.Image.new_from_icon_name("emblem-system-symbolic"))
    line.append(Gtk.Label(label="Nastavenia"))
    settings_button.set_child(line)
    settings_button.connect("clicked", lambda _b: (popover.popdown(), on_open(item)))
    popover.set_child(settings_button)
    popover.set_parent(tile)
    tile.connect("destroy", lambda _w: popover.unparent())

    def show_menu(_g, x, y):
        on_select(item)
        rect = Gdk.Rectangle()
        rect.x, rect.y, rect.width, rect.height = int(x), int(y), 1, 1
        popover.set_pointing_to(rect)
        popover.popup()

    right = Gtk.GestureClick(button=3)
    right.connect("pressed", lambda g, _n, x, y: show_menu(g, x, y))
    tile.add_controller(right)
    hold = Gtk.GestureLongPress()
    hold.set_touch_only(False)
    hold.connect("pressed", show_menu)
    tile.add_controller(hold)
    double = Gtk.GestureClick(button=1)
    double.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    double.connect("pressed", lambda _g, n, _x, _y: on_open(item) if n == 2 else None)
    tile.add_controller(double)
    return tile


def resources_grid(inventory, tab, on_select, on_open):
    """Zariadenia (alebo siete) ako dlaždice po skupinách (Správca zariadení, latte_common/hardware.py)."""
    body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    body.set_margin_top(6)
    body.set_margin_bottom(12)
    body.set_margin_start(12)
    body.set_margin_end(12)
    tiles = []

    def select(item):
        for other, tile in tiles:
            if other is item:
                tile.add_css_class("selected")
            else:
                tile.remove_css_class("selected")
        on_select(item)

    # Dva stĺpce skupín (malá skupina nezaberie celý riadok); skupina ide do nižšieho stĺpca, dlaždice zalamujú po troch.
    # Každá skupina je vlastná karta (.group-card): rámik okolo nadpisu a dlaždíc jednej kategórie.
    columns = [Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=GROUP_GAP) for _ in range(GROUP_COLUMNS)]
    heights = [0] * GROUP_COLUMNS
    for column in columns:
        column.set_size_request(TILES_PER_ROW * 124 + GROUP_PADDING, -1)
        column.set_valign(Gtk.Align.START)
    for gid, group_title, items in inventory.groups(tab):
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        section.add_css_class("group-card")
        section.set_name("group-%s" % gid)
        head = Gtk.Box(spacing=8)
        title = Gtk.Label(label=group_title.upper(), xalign=0, hexpand=True, ellipsize=3)
        title.add_css_class("section-title")
        head.append(title)
        if items:
            count = Gtk.Label(label=str(len(items)))
            count.add_css_class("group-count")
            head.append(count)
        section.append(head)
        if not items:
            note = placeholder_note(hardware.SHOW_EMPTY.get(gid, ""))
            note.set_max_width_chars(38)
            section.append(note)
        else:
            flow = Gtk.FlowBox(min_children_per_line=1, max_children_per_line=TILES_PER_ROW,
                               selection_mode=Gtk.SelectionMode.NONE, homogeneous=True)
            flow.set_halign(Gtk.Align.START)
            for item in items:
                tile = device_tile(item, select, on_open)
                tiles.append((item, tile))
                flow.append(tile)
            section.append(flow)
        lighter = heights.index(min(heights))
        columns[lighter].append(section)
        heights[lighter] += 1 + 3 * -(-max(len(items), 1) // TILES_PER_ROW)      # nadpis + riadky dlaždíc
    row = Gtk.Box(spacing=GROUP_GAP, halign=Gtk.Align.START, valign=Gtk.Align.START)
    for column in columns:
        row.append(column)
    body.append(row)

    scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
    scroll.set_child(body)
    return scroll


def placeholder_note(text):
    label = Gtk.Label(label=text, xalign=0, wrap=True)
    label.add_css_class("dim")
    label.set_margin_start(4)
    return label


class ResourcesBar(Gtk.Box):
    """Ovládanie vybraného zariadenia v ramene L: veľké tlačidlo Nastavenia (dotykovo aj myšou).

    Rovnaký panel je v pripnutom okne pod mapou. Bez výberu ukáže súhrn a čo sa nepodarilo zistiť.
    """

    def __init__(self, inventory, on_settings):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        self.inventory = inventory
        self.on_settings = on_settings
        self.item = None
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
        col.set_valign(Gtk.Align.CENTER)
        self.title = Gtk.Label(xalign=0, ellipsize=3)
        self.title.add_css_class("arm-title")
        self.line1 = Gtk.Label(xalign=0, ellipsize=3)
        self.line1.add_css_class("dim")
        self.line2 = Gtk.Label(xalign=0, wrap=True)
        self.line2.add_css_class("dim")
        col.append(self.title)
        col.append(self.line1)
        col.append(self.line2)
        self.append(col)
        self.button = Gtk.Button()
        self.button.add_css_class("arm-action")
        line = Gtk.Box(spacing=10)
        line.append(Gtk.Image.new_from_icon_name("emblem-system-symbolic"))
        line.append(Gtk.Label(label="Nastavenia"))
        self.button.set_child(line)
        self.button.set_valign(Gtk.Align.CENTER)
        self.button.set_size_request(170, 56)         # veľký cieľ pre prst
        self.button.connect("clicked", lambda _b: self.on_settings(self.item) if self.item else None)
        self.append(self.button)
        self.show_item(None)

    def show_item(self, item):
        self.item = item
        self.button.set_sensitive(item is not None)
        if item is None:
            total = len(self.inventory.items)
            groups = len(self.inventory.groups())
            self.title.set_text("%d zariadení v %d skupinách" % (total, groups))
            self.line1.set_text("Vyber zariadenie a klepni na Nastavenia (alebo naň klepni dvakrát).")
            problem = self.inventory.problems[0] if self.inventory.problems else ""
            self.line2.set_text(("! " + problem) if problem else "")
        else:
            group = hardware.GROUPS[item.group][0]
            self.title.set_text(item.name)
            self.line1.set_text(" · ".join(x for x in (group, item.status) if x))
            self.line2.set_text(item.detail)


# ---------------------------------------------------------------- mapa
class MapPanel(Gtk.Box):
    """Panel s dvoma záložkami a pripináčikom."""

    def __init__(self, kind, on_pin, on_launch, pinned=False, inventory=None, on_select=None, on_open=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.kind = kind
        self.on_launch = on_launch
        self.inventory = inventory
        self.on_select = on_select or (lambda _item: None)
        self.on_open = on_open or (lambda _item: None)
        self.add_css_class("map-panel")
        self.tab = 0

        if kind == "apps":
            titles = ("Nainštalované aplikácie", "Aplikácie bežiace na pozadí")
        else:
            titles = tuple(title for _tab, title in hardware.TABS)

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
            self.on_select(None)                # výber z inej záložky v ramene L neplatí
            content = resources_grid(self.inventory, hardware.TABS[idx][0], self.on_select, self.on_open)
        self.body.append(content)


def arm_box(kind, content=None):
    """Vodorovné rameno L so súhrnom. content: hotový obsah (zdroje: ResourcesBar)."""
    arm = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
    arm.add_css_class("arm")
    arm.set_size_request(-1, ARM_HEIGHT)
    if content is not None:
        arm.set_margin_start(20)
        arm.set_margin_end(COLUMN + 40)
        content.set_hexpand(True)
        arm.append(content)
        return arm

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

    def __init__(self, app, kind, on_launch, on_closed, on_settings=None):
        super().__init__(application=app)
        self.kind = kind
        self.on_closed = on_closed
        self.on_settings = on_settings
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

        if kind == "resources":
            self.inventory = hardware.scan()
            self.bar = ResourcesBar(self.inventory, self.open_settings)
            panel = MapPanel(kind, self.pin, on_launch, inventory=self.inventory,
                             on_select=self.bar.show_item, on_open=self.open_settings)
            arm = arm_box(kind, self.bar)
        else:
            panel = MapPanel(kind, self.pin, on_launch)
            arm = arm_box(kind)
        panel.set_size_request(MAP_WIDTH, MAP_HEIGHT)
        shape.append(panel)

        arm.set_size_request(MAP_WIDTH, ARM_HEIGHT)
        shape.append(arm)

        overlay.add_overlay(shape)

    def close_popup(self):
        self.on_closed()
        self.destroy()

    def open_settings(self, item):
        """Nastavenia vybraného zariadenia: stránka jeho skupiny, pri monitore rovno ten monitor."""
        if self.on_settings is not None:
            self.on_settings(item.settings_uri)
        self.close_popup()

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
        if kind == "resources":
            inventory = hardware.scan()
            self.bar = ResourcesBar(inventory, self.open_settings)
            self.bar.add_css_class("arm")
            self.bar.set_size_request(-1, ARM_HEIGHT)
            panel = MapPanel(kind, lambda: None, self.launch, pinned=True, inventory=inventory,
                             on_select=self.bar.show_item, on_open=self.open_settings)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            box.append(panel)
            box.append(self.bar)
            self.set_child(box)
        else:
            self.set_child(MapPanel(kind, lambda: None, self.launch, pinned=True))
        self.connect("close-request", self.on_close)

    def on_close(self, *_a):
        if self.on_closed is not None:
            self.on_closed(self.kind)
        return False

    def open_settings(self, item):
        opener = getattr(self.get_application(), "launch_settings", None)
        if opener is not None:
            opener(item.settings_uri)

    def launch(self, info):
        try:
            info.launch([], None)
        except GLib.Error:
            pass