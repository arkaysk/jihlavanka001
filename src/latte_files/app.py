#!/usr/bin/env python3
"""latte-files: správca súborov LatteOS (ForkLift model)."""
import errno
import grp
import os
import pwd
import stat
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Graphene", "1.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gtk, Gio, GLib, Gdk, GdkPixbuf, Graphene, Pango  # noqa: E402

from latte_common import fileops, favorites, jobs, places, prefs, storage, theme, thumbnails  # noqa: E402
from latte_common import volumes as vol_mod  # noqa: E402

ROOT_NAME = "Tento počítač"
PROGRESS_AFTER_MS = 300         # dialóg priebehu sa neukáže pri rýchlych operáciách
DENIED = (errno.EACCES, errno.EPERM)
ICON = 22                       # veľkosť ikony v zozname
COL_SIZE, COL_DATE, COL_KIND = 90, 140, 130
MODES = [
    ("simple", "sidebar-show-right-symbolic", "Jednoduché: jeden panel a inšpektor"),
    ("dual", "view-dual-symbolic", "Dvojpanel"),
    ("classic", "view-paged-symbolic", "Klasické: dvojpanel s textovou cestou"),
]
# Štýly zobrazenia zoznamu súborov: id, ikona tlačidla, názov, popis
VIEWS = [
    ("list", "view-list-symbolic", "Zoznam", "Názov vedľa malej ikony"),
    ("medium", "view-app-grid-symbolic", "Stredné ikony", "Názov pod ikonou"),
    ("details", "view-continuous-symbolic", "Podrobnosti", "Stĺpce: veľkosť, dátum, typ"),
    ("large", "image-x-generic-symbolic", "Miniatúry", "Náhľady fotiek a videí, inak veľké ikony"),
]
VIEW_IDS = [v[0] for v in VIEWS]
VIEW_ICON = {"list": 16, "details": ICON, "medium": 48, "large": 112}     # veľkosť ikony/náhľadu v px
CELL_WIDTH = {"medium": 104, "large": 144}                                # šírka bunky v mriežke
GRID_STYLES = ("medium", "large")
IMAGE_PREVIEW_MAX = 30 * 1024 * 1024
PREVIEW_W, PREVIEW_H = 248, 180


def free_space(path):
    try:
        st = os.statvfs(path)
        return GLib.format_size(st.f_bavail * st.f_frsize)
    except (OSError, TypeError):
        return ""


def fmt_time(epoch):
    try:
        stamp = GLib.DateTime.new_from_unix_local(int(epoch))
        return stamp.format("%-d. %-m. %Y %H:%M")
    except (OverflowError, TypeError, ValueError):
        return ""


def mtime(path):
    try:
        return fmt_time(os.path.getmtime(path))
    except OSError:
        return ""


def count_text(n, one, few, many):
    return "%d %s" % (n, one if n == 1 else few if 2 <= n <= 4 else many)


def kind_of(name, is_dir):
    """Druh položky podľa mena („Priečinok“, „Textový dokument“, …)."""
    if is_dir:
        return "Priečinok"
    ctype, _uncertain = Gio.content_type_guess(name, None)
    return Gio.content_type_get_description(ctype) if ctype else "Súbor"


def file_icon(name, is_dir):
    if is_dir:
        return Gtk.Image.new_from_icon_name("folder")
    ctype, _uncertain = Gio.content_type_guess(name, None)
    icon = Gio.content_type_get_icon(ctype) if ctype else None
    return Gtk.Image.new_from_gicon(icon) if icon else Gtk.Image.new_from_icon_name("text-x-generic")


ROW_TYPES = (Gtk.ListBoxRow, Gtk.FlowBoxChild)


class IconFlow(Gtk.FlowBox):
    """Mriežka ikon s rovnakými metódami na výber ako Gtk.ListBox, aby panel nemusel rozlišovať."""

    def select_row(self, row):
        self.select_child(row)

    def get_selected_rows(self):
        return self.get_selected_children()


def clear_rows(listbox):
    """Odstráni riadky zoznamu. Potomkom Gtk.ListBox je aj otvorený popover menu, ktorý
    sa cez remove() odstrániť nedá: slučka „kým je prvý potomok“ by sa zacyklila."""
    rows = []
    child = listbox.get_first_child()
    while child is not None:
        if isinstance(child, ROW_TYPES):
            rows.append(child)
        child = child.get_next_sibling()
    for row in rows:
        listbox.remove(row)


def popup_menu(parent, groups, x, y):
    """Kontextové menu: groups = [[(text, akcia), ...], ...], oddiely sa oddelia čiarou.

    Vlastný popover namiesto Gtk.PopoverMenu: ten má v GTK 4.22 pri prvom otvorení
    s oddielmi orezanú výšku (posledná položka zmizne).
    """
    popover = Gtk.Popover()
    popover.add_css_class("context-menu")
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    for group in groups:
        if box.get_first_child() is not None:
            box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        for label, action in group:
            btn = Gtk.Button(label=label)
            btn.add_css_class("flat")
            btn.get_child().set_xalign(0)
            btn.connect("clicked", lambda _b, a=action: (popover.popdown(), a()))
            box.append(btn)
    popover.set_child(box)
    first = box.get_first_child()

    spot = Gdk.Rectangle()
    spot.x, spot.y, spot.width, spot.height = int(x), int(y), 1, 1
    popover.set_parent(parent)
    popover.set_has_arrow(False)
    popover.set_halign(Gtk.Align.START)
    popover.set_pointing_to(spot)
    popover.connect("closed", lambda p: GLib.idle_add(p.unparent))
    popover.popup()
    if first is not None:
        first.grab_focus()


def dim_label(text="", xalign=0.0, width=None):
    lbl = Gtk.Label(label=text, xalign=xalign)
    lbl.add_css_class("dim-label")
    lbl.set_ellipsize(3)
    if width:
        lbl.set_size_request(width, -1)
    return lbl


# ------------------------------------------------------------------ panel
class Pane(Gtk.Box):
    COLUMNS = [("name", "Názov"), ("size", "Veľkosť"), ("date", "Zmenené"), ("kind", "Typ")]

    def __init__(self, window, volumes, style="details"):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("pane")
        self.win = window
        self.volumes = volumes
        self.view_style = style if style in VIEW_IDS else "details"

        self.volume = None
        self.path = None
        self.root = None
        self.admin = False          # výpis priečinka cez správcovského pomocníka
        self.generation = 0         # zahodí oneskorenú odpoveď po zmene priečinka
        self.sort_key = "name"
        self.sort_desc = False
        self.compact = False        # v dvojpaneli sa stĺpec Typ skrýva (úzke panely)
        self.history = []
        self.forward = []

        # oranžová čiara aktívneho panela (ako v ForkLifte)
        bar = Gtk.Box()
        bar.add_css_class("active-bar")
        self.append(bar)

        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        head.add_css_class("pane-head")
        self.head_icon = Gtk.Image()
        self.head_icon.set_pixel_size(36)
        head.append(self.head_icon)

        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
        text.set_valign(Gtk.Align.CENTER)
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.crumbs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.text_path = Gtk.Label(xalign=0)
        self.text_path.set_ellipsize(3)
        self.badge = Gtk.Label(label="Správca")
        self.badge.add_css_class("admin-badge")
        self.badge.set_visible(False)
        top.append(self.crumbs)
        top.append(self.text_path)
        top.append(self.badge)
        self.status = dim_label()
        text.append(top)
        text.append(self.status)
        head.append(text)
        self.append(head)

        # záhlavie stĺpcov, kliknutím sa mení triedenie
        cols = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cols.add_css_class("column-head")
        self.col_labels = {}
        widths = {"name": None, "size": COL_SIZE, "date": COL_DATE, "kind": COL_KIND}
        for key, title in self.COLUMNS:
            lbl = Gtk.Label(label=title, xalign=1 if key == "size" else 0)
            if widths[key]:
                lbl.set_size_request(widths[key], -1)
            else:
                lbl.set_hexpand(True)
                lbl.set_margin_start(ICON + 10)
            click = Gtk.GestureClick()
            click.connect("pressed", lambda _g, _n, _x, _y, k=key: self.set_sort(k))
            lbl.add_controller(click)
            cols.append(lbl)
            self.col_labels[key] = lbl
        self.cols = cols
        self.append(cols)

        # dva kontajnery: riadky (Zoznam, Podrobnosti) a mriežka (Stredné ikony, Miniatúry);
        # self.list je vždy ten práve zobrazený, ostatný kód s ním pracuje rovnako
        self.scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        self.listbox = Gtk.ListBox()
        self.flow = IconFlow()
        self.flow.add_css_class("icon-grid")
        self.flow.set_homogeneous(True)
        self.flow.set_valign(Gtk.Align.START)       # riadky sa neroztiahnu; pravý klik pod nimi chytá scroll
        self.flow.set_min_children_per_line(1)
        self.flow.set_max_children_per_line(60)
        self.flow.set_row_spacing(6)
        self.flow.set_column_spacing(4)
        self.listbox.connect("row-activated", self.on_activate)
        self.listbox.connect("selected-rows-changed", self.on_selection_changed)
        self.flow.connect("child-activated", self.on_activate)
        self.flow.connect("selected-children-changed", self.on_selection_changed)
        for container in (self.listbox, self.flow):
            container.add_css_class("files-list")
            container.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
            container.set_activate_on_single_click(False)       # otvára sa dvojklikom, klik len vyberá
        # pravý klik chytá celý posuvný panel (aj prázdne miesto pod ikonami), nie kontajner
        context = Gtk.GestureClick()
        context.set_button(3)
        context.connect("pressed", self.on_scroll_context)
        self.scroll.add_controller(context)
        self.list = self.flow if self.view_style in GRID_STYLES else self.listbox
        self.scroll.set_child(self.list)
        self.cols.set_visible(self.view_style == "details")
        self.append(self.scroll)

        click = Gtk.GestureClick()
        click.connect("pressed", lambda *_a: self.win.set_active(self))
        self.add_controller(click)

        self.update_sort_labels()
        self.go_root(record=False)

    def on_selection_changed(self, *_a):
        self.update_status()
        self.win.update_detail()

    # -------- triedenie --------
    def set_sort(self, key):
        if self.sort_key == key:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_key, self.sort_desc = key, False
        self.update_sort_labels()
        self.refresh()

    def update_sort_labels(self):
        for key, title in self.COLUMNS:
            arrow = (" ▼" if self.sort_desc else " ▲") if key == self.sort_key else ""
            self.col_labels[key].set_text(title + arrow)

    def sorted_entries(self, entries):
        """Priečinky vždy prvé; v skupinách podľa zvoleného stĺpca."""
        def key_of(e):
            if self.sort_key == "size":
                return (e["size"], e["name"].casefold())
            if self.sort_key == "date":
                return (e["mtime"], e["name"].casefold())
            if self.sort_key == "kind":
                return (kind_of(e["name"], e["is_dir"]).casefold(), e["name"].casefold())
            return (e["name"].casefold(),)

        dirs = [e for e in entries if e["is_dir"]]
        files = [e for e in entries if not e["is_dir"]]
        # priečinky nemajú veľkosť: pri triedení podľa veľkosti idú podľa mena
        dir_key = (lambda e: (e["name"].casefold(),)) if self.sort_key == "size" else key_of
        return (sorted(dirs, key=dir_key, reverse=self.sort_desc)
                + sorted(files, key=key_of, reverse=self.sort_desc))

    # -------- štýl zobrazenia --------
    def set_view_style(self, style):
        if style not in VIEW_IDS or style == self.view_style:
            return
        self.view_style = style
        self.list = self.flow if style in GRID_STYLES else self.listbox
        self.scroll.set_child(self.list)
        self.cols.set_visible(style == "details")
        self.win.on_view_style_changed(self)
        self.refresh()

    def row_at(self, x, y):
        """Riadok alebo ikona pod bodom (súradnice sú vzhľadom na self.list)."""
        if self.list is self.flow:
            return self.flow.get_child_at_pos(int(x), int(y))
        return self.list.get_row_at_y(int(y))

    # -------- filter (vyhľadávanie) --------
    def set_filter(self, text):
        text = text.strip().casefold()
        self.list.unselect_all()
        func = (lambda row: row.kind != "item" or text in row.name.casefold()) if text else None
        for container in (self.listbox, self.flow):
            container.set_filter_func(func)
            container.invalidate_filter()

    # -------- navigácia --------
    def snapshot(self):
        return (self.volume, self.path, self.root)

    def record(self):
        self.history.append(self.snapshot())
        self.forward.clear()

    def go_root(self, record=True):
        if record and self.volume is not None:
            self.record()
        self.volume = None
        self.path = None
        self.root = None
        self.admin = False
        self.refresh()

    def go_volume(self, volume, record=True):
        if not volume.mounted:
            if volume.mountable:
                # nepripojený zväzok sa pripojí pri otvorení a potom sa doň vstúpi
                self.win.mount_volume(volume, lambda v: self.go_volume(v, record))
            else:
                # prázdny disk, mechanika bez média, šifrovaný zväzok, disketa bez ovládača
                self.win.notify("„%s“ (%s): %s" % (volume.name, volume.kind_text.lower(), volume.help_text))
            return
        if record:
            self.record()
        self.volume = volume
        self.path = volume.path
        self.root = volume.path
        self.admin = False
        self.refresh()

    def go_path(self, path, root=None, record=True):
        if record:
            self.record()
        if root is not None:
            self.root = root
        self.path = path
        self.refresh()

    def open_location(self, volume, path, root):
        """Skok na cestu vo zväzku (obľúbené položky)."""
        self.record()
        self.volume, self.path, self.root = volume, path, root
        self.admin = False
        self.refresh()

    def usable(self, snap):
        """Záznam histórie je použiteľný, len ak jeho zväzok stále existuje a je pripojený."""
        volume = snap[0]
        if volume is None:
            return True
        return any(v == volume and v.mounted and v.path == volume.path for v in self.volumes)

    def back(self):
        while self.history:
            snap = self.history.pop()
            if self.usable(snap):
                self.forward.append(self.snapshot())
                self.volume, self.path, self.root = snap
                self.admin = False
                self.refresh()
                return

    def ahead(self):
        while self.forward:
            snap = self.forward.pop()
            if self.usable(snap):
                self.history.append(self.snapshot())
                self.volume, self.path, self.root = snap
                self.admin = False
                self.refresh()
                return

    def up(self):
        if self.volume is None:
            return
        if self.path == self.root:
            if self.root != self.volume.path:
                self.record()
                self.path = self.volume.path
                self.root = self.volume.path
                self.refresh()
            else:
                self.go_root()
            return
        self.go_path(places.parent(self.path))

    def rebind(self):
        """Po zmene zoznamu zväzkov: nová inštancia toho istého zväzku. Ak zmizol
        alebo sa odpojil, pane sa vráti do koreňa; vráti jeho meno, inak None."""
        old = self.volume
        if old is None:
            return None
        for v in self.volumes:
            if v == old and v.mounted:
                self.volume = v
                if v.path != old.path:
                    self.path = self.root = v.path
                return None
        self.go_root(record=False)
        return old.name

    def title_text(self):
        if self.volume is None:
            return ROOT_NAME
        if self.path == self.volume.path:
            return self.volume.name
        return places.title(self.path)

    # -------- otvorenie --------
    def on_activate(self, _box, row):
        self.win.set_active(self)
        self.open_row(row)

    def open_selected(self):
        rows = self.list.get_selected_rows()
        if len(rows) == 1:
            self.open_row(rows[0])

    def open_row(self, row):
        if row.volume is not None:
            self.go_volume(row.volume)
            return
        if row.kind == "admin":
            self.load_admin()
            return
        target = row.target
        if not target:
            return
        if os.path.isdir(target) or row.is_dir:
            if self.path == self.volume.path and self.volume.entries() is not None:
                self.go_path(target, root=target)
            else:
                self.go_path(target)
            return
        self.win.open_object(target)

    # -------- výber --------
    def selection(self):
        """Cesty vybraných súborov a priečinkov, na ktorých sa dajú robiť operácie."""
        return [r.target for r in self.list.get_selected_rows() if r.kind == "item" and r.target]

    def detail_items(self):
        """(cesta, je priečinok) všetkého vybraného, čo má cieľ (aj pevné miesta)."""
        return [(r.target, r.is_dir) for r in self.list.get_selected_rows() if r.target]

    def can_write(self):
        return self.volume is not None and self.path is not None and not self.at_fixed_root()

    def at_fixed_root(self):
        """Koreň zväzku, ktorý ukazuje len vybrané miesta (systémový zväzok)."""
        return (
            self.volume is not None
            and self.path == self.volume.path
            and self.volume.entries() is not None
        )

    # -------- kontextové menu --------
    def on_scroll_context(self, gesture, n, x, y):
        """Súradnice z posuvného panela sa prepočítajú na súradnice zobrazeného kontajnera."""
        ok, point = self.scroll.compute_point(self.list, Graphene.Point().init(x, y))
        self.on_context(gesture, n, point.x if ok else x, point.y if ok else y)

    def on_context(self, _gesture, _n, x, y):
        row = self.row_at(x, y)
        if row is not None and row.volume is not None:
            return                      # zväzok má vlastné menu
        self.win.set_active(self)

        if row is not None and row.kind in ("item", "fixed") and row.target:
            if not row.is_selected():
                self.list.unselect_all()
                self.list.select_row(row)
            groups = self.item_menu()
        elif row is None and self.can_write():
            self.list.unselect_all()
            groups = self.blank_menu()
        else:
            return
        popup_menu(self.list, groups, x, y)

    def item_menu(self):
        win = self.win
        rows = self.list.get_selected_rows()
        items = self.selection()
        if len(rows) == 1:
            row = rows[0]
            groups = [[("Otvoriť", self.open_selected)]]
            if row.is_dir:
                groups[0].append(self.favorite_entry(row.target))
            if row.kind == "item":
                groups.append([
                    ("Premenovať", win.do_rename),
                    ("Kopírovať do druhého panela", win.do_copy),
                    ("Presunúť do druhého panela", win.do_move),
                ])
                groups.append([("Do koša", win.do_trash)])
            return groups
        n = count_text(len(items), "položku", "položky", "položiek")
        return [
            [("Kopírovať %s do druhého panela" % n, win.do_copy),
             ("Presunúť %s do druhého panela" % n, win.do_move)],
            [("Presunúť %s do koša" % n, win.do_trash)],
        ]

    def blank_menu(self):
        groups = [[("Nový priečinok", self.win.do_mkdir)]]
        groups.append([self.favorite_entry(self.path, "aktuálny priečinok")])
        return groups

    def favorite_entry(self, path, what=None):
        if path in favorites.load():
            return ("Odobrať z obľúbených", lambda: self.win.remove_favorite(path))
        text = "Pridať medzi obľúbené" + (": " + what if what else "")
        return (text, lambda: self.win.add_favorite(path))

    # -------- breadcrumb --------
    def crumb_button(self, label, action):
        btn = Gtk.Button(label=label)
        btn.add_css_class("flat")
        btn.add_css_class("crumb")
        btn.connect("clicked", action)
        return btn

    def build_crumbs(self):
        child = self.crumbs.get_first_child()
        while child is not None:
            self.crumbs.remove(child)
            child = self.crumbs.get_first_child()

        show = self.win.mode != "classic"
        self.crumbs.set_visible(show)
        self.text_path.set_visible(not show)

        if not show:
            if self.volume is None:
                self.text_path.set_text(ROOT_NAME)
            else:
                base = os.path.dirname(self.root) if self.root != self.volume.path else self.volume.path
                names = [n for n, _p in places.parts(base, self.path)]
                self.text_path.set_text("/".join([self.volume.name] + names))
            return

        self.crumbs.append(self.crumb_button(ROOT_NAME, lambda _b: self.go_root()))
        if self.volume is None:
            return

        vol = self.volume
        self.crumbs.append(Gtk.Label(label="›"))
        self.crumbs.append(self.crumb_button(vol.name, lambda _b, v=vol: self.go_volume(v)))
        if self.path == vol.path:
            return

        if self.root != vol.path:
            base = self.root
            self.crumbs.append(Gtk.Label(label="›"))
            self.crumbs.append(
                self.crumb_button(
                    os.path.basename(self.root),
                    lambda _b, p=self.root: self.go_path(p, root=p),
                )
            )
        else:
            base = vol.path

        for part, current in places.parts(base, self.path):
            self.crumbs.append(Gtk.Label(label="›"))
            self.crumbs.append(
                self.crumb_button(part, lambda _b, p=current: self.go_path(p))
            )

    # -------- výpis --------
    def add_row(self, text, size, date, target, volume=None, is_dir=False, kind="item",
                kind_text="", size_bytes=0, icon=None, subtitle=""):
        # kind: item = súbor alebo priečinok, fixed = pevné miesto v koreni
        # systémového zväzku (len otvoriť), parent = riadok „..“,
        # admin = výzva zobraziť ako správca, note = len text
        style = self.view_style
        grid = style in GRID_STYLES
        row = Gtk.FlowBoxChild() if grid else Gtk.ListBoxRow()
        row.target = target
        row.volume = volume
        row.is_dir = is_dir
        row.kind = kind
        row.name = text
        row.size_bytes = size_bytes

        if icon is None:
            if volume is not None:
                icon = Gtk.Image.new_from_icon_name(volume.icon_name)
            elif kind == "admin":
                icon = Gtk.Image.new_from_icon_name("dialog-password-symbolic")
            elif kind == "parent":
                icon = Gtk.Image.new_from_icon_name("go-up-symbolic")
            else:
                icon = file_icon(text, is_dir)
        icon.set_pixel_size(VIEW_ICON[style])
        detail = " · ".join(x for x in (size, date, kind_text) if x)

        if grid:
            cell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            cell.add_css_class("icon-cell")
            cell.set_size_request(CELL_WIDTH[style], -1)
            slot = Gtk.Box(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
            slot.set_size_request(-1, VIEW_ICON[style] + 6)
            slot.append(icon)
            label = Gtk.Label(label=text, wrap=True, justify=Gtk.Justification.CENTER)
            label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
            label.set_lines(2)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_max_width_chars(14 if style == "medium" else 18)
            cell.append(slot)
            cell.append(label)
            if subtitle:
                sub_label = dim_label(subtitle, 0.5)
                sub_label.set_justify(Gtk.Justification.CENTER)
                cell.append(sub_label)
            row.set_child(cell)
            row.set_tooltip_text(text + ("\n" + detail if detail else ""))
        else:
            line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            pad = 2 if style == "list" else 4
            line.set_margin_top(pad)
            line.set_margin_bottom(pad)
            line.set_margin_start(12)
            line.set_margin_end(12)
            line.append(icon)
            name = Gtk.Label(label=text, xalign=0, hexpand=True)
            name.set_ellipsize(3)
            line.append(name)
            if style == "details":
                line.append(dim_label(size, 1, COL_SIZE))
                line.append(dim_label(date, 0, COL_DATE))
                if not self.compact:
                    line.append(dim_label(kind_text, 0, COL_KIND))
            elif detail:
                row.set_tooltip_text(text + "\n" + detail)
            row.set_child(line)
            if kind == "note":
                row.set_selectable(False)
                row.set_activatable(False)

        self.list.append(row)
        if style == "large" and kind == "item" and not is_dir and target and thumbnails.wants_thumbnail(target):
            self.load_thumbnail(icon, target)
        return row

    def load_thumbnail(self, icon, path):
        """Fotku alebo video nahradí ikonu náhľadom, keď je pripravený (vo vlákne)."""
        gen = self.generation

        def ready(pixbuf):
            if pixbuf is not None:
                icon.set_from_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
                icon.set_pixel_size(max(pixbuf.get_width(), pixbuf.get_height()))

        thumbnails.request(path, VIEW_ICON["large"], ready,
                           lambda: gen == self.generation and self.view_style == "large")

    def clear(self):
        clear_rows(self.listbox)
        clear_rows(self.flow)

    def update_status(self):
        """Druhý riadok hlavičky: počet položiek, výber a voľné miesto."""
        if self.volume is None:
            self.status.set_text(count_text(len(self.volumes), "zariadenie", "zariadenia", "zariadení"))
            return
        rows = []
        child = self.list.get_first_child()
        while child is not None:
            if isinstance(child, ROW_TYPES) and child.kind in ("item", "fixed"):
                rows.append(child)
            child = child.get_next_sibling()
        selected = [r for r in self.list.get_selected_rows() if r.kind in ("item", "fixed")]
        if selected:
            total = sum(r.size_bytes for r in selected)
            text = "vybraných %d z %d" % (len(selected), len(rows))
            if total:
                text += " (%s)" % GLib.format_size(total)
        else:
            text = count_text(len(rows), "položka", "položky", "položiek")
        space = free_space(self.path)
        if space:
            text += ", " + space + " voľné"
        self.status.set_text(text)

    def refresh(self):
        self.generation += 1
        self.compact = self.win.mode != "simple" and self.view_style == "details"
        self.col_labels["kind"].set_visible(not self.compact)
        self.clear()
        self.build_crumbs()

        if self.admin and os.access(self.path or "/", os.R_OK | os.X_OK):
            self.admin = False          # už sa dá čítať aj bez správcu
        self.badge.set_visible(self.admin)

        if self.volume is None:
            self.head_icon.set_from_icon_name("computer")
        elif self.path == self.volume.path:
            self.head_icon.set_from_icon_name(self.volume.icon_name)
        elif self.path == places.trash_files():
            self.head_icon.set_from_icon_name("user-trash-full" if places.count_trashed() else "user-trash")
        else:
            self.head_icon.set_from_icon_name("folder-open")
        self.win.update_title()

        if self.volume is None:
            for v in self.volumes:
                if v.mounted:
                    note = free_space(v.path)
                    text = ("voľné " + note + " z " + v.size) if note else v.size
                else:
                    text = " · ".join(x for x in (v.state_text, v.size) if x)
                kind_text = v.kind_text + (" · " + v.label if v.label else "")
                row = self.add_row(v.name, text, "", None, volume=v, kind_text=kind_text, subtitle=text)
                self.win.attach_volume_menu(row, v)
            self.finish_refresh()
            return

        if self.path == self.volume.path:
            custom = self.volume.entries()
            if custom is not None:
                for label, target in custom:
                    self.add_row(label, "", mtime(target), target, is_dir=True, kind="fixed",
                                 kind_text="Priečinok")
                self.finish_refresh()
                return

        if self.path != self.root:
            self.add_row("..", "", "", places.parent(self.path), is_dir=True, kind="parent")

        if self.admin:
            self.list_as_admin()
            return

        try:
            entries = []
            with os.scandir(self.path) as it:
                for entry in it:
                    try:
                        is_dir = entry.is_dir()
                        st = entry.stat()
                        entries.append({"name": entry.name, "path": entry.path, "is_dir": is_dir,
                                        "size": 0 if is_dir else st.st_size, "mtime": st.st_mtime})
                    except OSError:
                        entries.append({"name": entry.name, "path": entry.path, "is_dir": False,
                                        "size": 0, "mtime": 0})
        except PermissionError:
            denied = "Prístup odmietnutý"
            if self.volume.fstype == "vboxsf":
                denied += " (zdieľaný priečinok VirtualBoxu patrí skupine vboxsf, pridajte do nej používateľa)"
            if jobs.admin_available():
                self.add_row(denied + ". Dvojklik: zobraziť ako správca", "", "", None, kind="admin")
            else:
                self.add_row(denied, "", "", None, kind="note")
            self.finish_refresh()
            return
        except FileNotFoundError:
            self.add_row("Priečinok už neexistuje", "", "", None, kind="note")
            self.finish_refresh()
            return

        self.fill_entries(entries)

    def fill_entries(self, entries):
        if self.path == places.home() and not self.admin:
            self.add_trash_row()
        for e in self.sorted_entries(entries):
            if e["name"].startswith("."):
                continue
            self.add_row(
                e["name"], "" if e["is_dir"] else GLib.format_size(e["size"]), fmt_time(e["mtime"]),
                e["path"], is_dir=e["is_dir"], kind_text=kind_of(e["name"], e["is_dir"]),
                size_bytes=e["size"])
        self.finish_refresh()

    def add_trash_row(self):
        """Kôš ako zložka v súkromnom priestore (skutočne leží v ~/.local/share/Trash/files)."""
        count = places.count_trashed()
        icon = Gtk.Image.new_from_icon_name("user-trash-full" if count else "user-trash")
        self.add_row(places.TRASH_NAME, "", mtime(places.trash_files()), places.trash_files(), is_dir=True,
                     kind="fixed", kind_text="Kôš · " + count_text(count, "položka", "položky", "položiek"),
                     icon=icon)

    def finish_refresh(self):
        self.update_status()
        self.win.update_detail()

    # -------- výpis ako správca --------
    def load_admin(self):
        """Dvojklik na „Prístup odmietnutý“: obsah priečinka prečíta pomocník cez pkexec."""
        self.admin = True
        self.refresh()

    def list_as_admin(self):
        gen = self.generation
        loading = self.add_row("Čaká sa na oprávnenie správcu…", "", "", None, kind="note")

        def done(res):
            if gen != self.generation:
                return                  # medzitým sa prešlo inam
            state = res.get("state")
            if state == "done":
                self.list.remove(loading)
                entries = [{"name": e["name"], "path": os.path.join(self.path, e["name"]),
                            "is_dir": e["is_dir"], "size": e["size"], "mtime": e["mtime"]}
                           for e in res.get("entries", [])]
                self.fill_entries(entries)
                return
            self.admin = False
            if state == "error":
                err = res.get("error") or ["", 0, "neznáma chyba"]
                self.win.notify("Obsah sa nepodarilo zobraziť ako správca: %s" % err[2])
            self.refresh()

        jobs.call(["list", self.path], done)


# ------------------------------------------------------------------ inšpektor
class Detail(Gtk.Box):
    """Pravý panel: náhľad, názov a údaje o vybranej položke (ako inšpektor ForkLiftu)."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add_css_class("files-inspector")
        self.set_size_request(280, -1)
        self.set_hexpand(False)         # popisky s hexpand by z panela urobili polovicu okna

        self.icon = Gtk.Image()
        self.icon.set_pixel_size(96)
        self.icon.set_margin_top(24)
        # Gtk.Image, nie Gtk.Picture: šírka Picture závisí od výšky a rozťahovala by celý panel
        self.picture = Gtk.Image()
        self.picture.set_size_request(-1, PREVIEW_H)
        self.picture.set_margin_top(16)
        self.picture.set_margin_start(16)
        self.picture.set_margin_end(16)
        self.picture.add_css_class("preview")
        self.title = Gtk.Label(wrap=True, xalign=0)
        self.title.set_max_width_chars(24)      # obmedzí prirodzenú šírku panela
        self.title.add_css_class("inspector-title")
        self.title.set_margin_start(18)
        self.title.set_margin_end(18)
        self.title.set_margin_top(10)
        self.subtitle = dim_label()
        self.subtitle.set_max_width_chars(32)
        self.subtitle.set_margin_start(18)
        self.subtitle.set_margin_end(18)
        self.rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.rows.set_margin_start(18)
        self.rows.set_margin_end(18)
        self.rows.set_margin_top(14)
        for w in (self.icon, self.picture, self.title, self.subtitle, self.rows):
            self.append(w)

    def fill(self, sections):
        """sections = [(nadpis, [(kľúč, hodnota), ...]), ...]"""
        child = self.rows.get_first_child()
        while child is not None:
            self.rows.remove(child)
            child = self.rows.get_first_child()
        for heading, info in sections:
            title = Gtk.Label(label=heading, xalign=0)
            title.add_css_class("section-title")
            self.rows.append(title)
            for key, value in info:
                line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                line.add_css_class("inspector-row")
                k = dim_label(key)
                k.add_css_class("detail-key")
                v = Gtk.Label(label=value, xalign=1, hexpand=True)
                v.set_ellipsize(1)          # začiatok cesty sa skráti, koniec ostane
                v.set_max_width_chars(26)
                v.add_css_class("detail-key")
                v.set_tooltip_text(value)
                line.append(k)
                line.append(v)
                self.rows.append(line)

    def show_preview(self, path, is_dir):
        """Obrázky sa ukážu zväčšené; ostatné veľkou ikonou druhu súboru."""
        image = False
        if not is_dir:
            ctype, _u = Gio.content_type_guess(path, None)
            try:
                image = (ctype or "").startswith("image/") and "svg" not in ctype \
                    and os.path.getsize(path) <= IMAGE_PREVIEW_MAX
            except OSError:
                image = False
        self.picture.set_visible(image)
        self.icon.set_visible(not image)
        if image:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, PREVIEW_W, PREVIEW_H, True)
                self.picture.set_from_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
            except GLib.Error:
                image = False           # nečitateľný obrázok: ukáže sa ikona
                self.picture.set_visible(False)
                self.icon.set_visible(True)
        if image:
            pass
        elif is_dir:
            self.icon.set_from_icon_name("folder")
        else:
            ctype, _u = Gio.content_type_guess(path, None)
            gicon = Gio.content_type_get_icon(ctype) if ctype else None
            if gicon:
                self.icon.set_from_gicon(gicon)
            else:
                self.icon.set_from_icon_name("text-x-generic")

    def show_items(self, items):
        """items = [(cesta, je priečinok)] vybraného v aktívnom paneli."""
        if not items:
            self.picture.set_visible(False)
            self.icon.set_visible(True)
            self.icon.set_from_icon_name("folder")
            self.title.set_text("Nič nie je vybrané")
            self.subtitle.set_text("")
            self.fill([])
            return
        if len(items) == 1:
            path, is_dir = items[0]
            self.show_preview(path, is_dir)
            name = os.path.basename(path) or path
            self.title.set_text(name)
            general = [("Cesta", os.path.dirname(path) or "/")]
            perms = []
            size_text = ""
            try:
                st = os.stat(path)
                if not is_dir:
                    size_text = GLib.format_size(st.st_size)
                    general.append(("Veľkosť", size_text))
                general.append(("Zmenené", fmt_time(st.st_mtime)))
                try:
                    owner = pwd.getpwuid(st.st_uid).pw_name
                except KeyError:
                    owner = str(st.st_uid)
                try:
                    group = grp.getgrgid(st.st_gid).gr_name
                except KeyError:
                    group = str(st.st_gid)
                perms = [("Práva", "%s (%o)" % (stat.filemode(st.st_mode), stat.S_IMODE(st.st_mode))),
                         ("Vlastník", owner), ("Skupina", group)]
            except OSError:
                pass
            kind = kind_of(name, is_dir)
            self.subtitle.set_text(kind + (" · " + size_text if size_text else ""))
            sections = [("Všeobecné", general)]
            if perms:
                sections.append(("Oprávnenia", perms))
            self.fill(sections)
            return

        dirs = sum(1 for _p, d in items if d)
        files = len(items) - dirs
        total = 0
        for path, is_dir in items:
            if not is_dir:
                try:
                    total += os.path.getsize(path)
                except OSError:
                    pass
        self.picture.set_visible(False)
        self.icon.set_visible(True)
        self.icon.set_from_icon_name("view-list-symbolic")
        self.title.set_text("Vybraných: %d" % len(items))
        self.subtitle.set_text("")
        info = []
        if files:
            info.append(("Súbory", str(files)))
        if dirs:
            info.append(("Priečinky", str(dirs)))
        if files:
            info.append(("Veľkosť súborov", GLib.format_size(total)))
        self.fill([("Výber", info)])


# ------------------------------------------------------------------ priebeh
class ProgressDialog(Gtk.Window):
    def __init__(self, parent, title, on_cancel):
        super().__init__(transient_for=parent, modal=True, title=title)
        self.set_default_size(440, -1)
        self.set_deletable(False)
        self.on_cancel = on_cancel
        self.cancelling = False

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for f in (box.set_margin_top, box.set_margin_bottom, box.set_margin_start, box.set_margin_end):
            f(18)
        self.name = Gtk.Label(label="Príprava…", xalign=0)
        self.name.set_ellipsize(3)
        self.bar = Gtk.ProgressBar()
        self.detail = Gtk.Label(label="", xalign=0)
        self.detail.add_css_class("dim-label")
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, halign=Gtk.Align.END)
        self.cancel_btn = Gtk.Button(label="Zrušiť")
        self.cancel_btn.connect("clicked", self.cancel)
        row.append(self.cancel_btn)
        for w in (self.name, self.bar, self.detail, row):
            box.append(w)
        self.set_child(box)

    def cancel(self, *_a):
        self.cancelling = True
        self.cancel_btn.set_sensitive(False)
        self.name.set_text("Ruší sa…")
        self.on_cancel()

    def update(self, p):
        if p.current and not self.cancelling:
            self.name.set_text(p.current)
        if p.bytes_total:
            fraction = p.bytes_done / p.bytes_total
            text = "%s z %s" % (GLib.format_size(p.bytes_done), GLib.format_size(p.bytes_total))
        elif p.items_total:
            fraction = p.items_done / p.items_total
            text = ""
        else:
            fraction, text = 0.0, ""
        if p.items_total > 1:
            text += (" · " if text else "") + "položka %d z %d" % (min(p.items_done + 1, p.items_total), p.items_total)
        self.bar.set_fraction(min(1.0, fraction))
        self.detail.set_text(text)


# ------------------------------------------------------------------ okno
def tool_button(icon, tooltip, action):
    btn = Gtk.Button(icon_name=icon)
    btn.set_tooltip_text(tooltip)
    btn.add_css_class("flat")
    btn.connect("clicked", lambda _b: action())
    return btn


def linked(*widgets):
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    box.add_css_class("linked")
    box.add_css_class("tool-group")
    for w in widgets:
        box.append(w)
    return box


class Window(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Súbory")
        self.add_css_class("latte-files")
        self.set_default_size(1280, 760)
        self.volumes = vol_mod.list_volumes()
        trash_problem = places.ensure_trash()
        if trash_problem:
            print("latte-files:", trash_problem, file=sys.stderr)
        self.mode = "simple"        # simple | dual | classic
        self.prefs = prefs.load("files")

        # ---- panel nástrojov (ako v ForkLifte: navigácia, názov, zobrazenie, akcie, hľadanie)
        header = Gtk.HeaderBar()
        header.add_css_class("files-toolbar")
        header.add_css_class("latte-titlebar")      # výšku určuje Prispôsobenie (latte.css), nie gtk.css
        self.set_titlebar(header)

        self.btn_back = tool_button("go-previous-symbolic", "Späť", lambda: self.active.back())
        self.btn_fwd = tool_button("go-next-symbolic", "Dopredu", lambda: self.active.ahead())
        btn_up = tool_button("go-up-symbolic", "O úroveň vyššie (Backspace)", lambda: self.active.up())
        header.pack_start(linked(self.btn_back, self.btn_fwd, btn_up))

        self.title_label = Gtk.Label(label=ROOT_NAME)
        self.title_label.add_css_class("toolbar-title")
        header.set_title_widget(self.title_label)

        self.search = Gtk.SearchEntry(placeholder_text="Hľadať")
        self.search.set_size_request(190, -1)
        self.search.connect("search-changed", self.on_search)
        self.search.connect("stop-search", lambda e: e.set_text(""))
        header.pack_end(self.search)

        self.btn_star = tool_button("non-starred-symbolic", "Pridať aktuálny priečinok medzi obľúbené",
                                    self.toggle_current_favorite)
        header.pack_end(linked(
            tool_button("view-refresh-symbolic", "Obnoviť", self.refresh_all),
            tool_button("edit-copy-symbolic", "Kopírovať do druhého panela (F5)", lambda: self.do_copy()),
            tool_button("folder-new-symbolic", "Nový priečinok (F7)", lambda: self.do_mkdir()),
            tool_button("user-trash-symbolic", "Do koša (F8)", lambda: self.do_trash()),
        ))
        header.pack_end(linked(self.btn_star))

        self.mode_buttons = {}
        first = None
        for mode, icon, tip in MODES:
            btn = Gtk.ToggleButton(icon_name=icon)
            btn.set_tooltip_text(tip)
            if first is None:
                first = btn
            else:
                btn.set_group(first)
            btn.connect("toggled", lambda b, m=mode: b.get_active() and self.set_mode(m))
            self.mode_buttons[mode] = btn
        header.pack_end(linked(*self.mode_buttons.values()))

        # štýl zobrazenia zoznamu súborov (Zoznam, Stredné ikony, Podrobnosti, Miniatúry)
        self.view_button = Gtk.MenuButton()
        self.view_button.add_css_class("flat")
        popover = Gtk.Popover()
        popover.add_css_class("context-menu")
        menu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.view_checks = {}
        for style, icon, title, hint in VIEWS:
            item = Gtk.Button()
            item.add_css_class("flat")
            line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            line.append(Gtk.Image.new_from_icon_name(icon))
            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1, hexpand=True)
            name = Gtk.Label(label=title, xalign=0)
            text.append(name)
            text.append(dim_label(hint))
            line.append(text)
            check = Gtk.Image.new_from_icon_name("object-select-symbolic")
            line.append(check)
            item.set_child(line)
            item.connect("clicked", lambda _b, st=style: (popover.popdown(), self.set_view_style(st)))
            menu.append(item)
            self.view_checks[style] = check
        popover.set_child(menu)
        self.view_button.set_popover(popover)
        header.pack_end(linked(self.view_button))

        # ---- telo
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(body)

        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        side.add_css_class("files-sidebar")
        side.set_size_request(250, -1)
        side_scroll = Gtk.ScrolledWindow(vexpand=True)
        side_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        side_scroll.set_child(side_box)
        side.append(side_scroll)

        head_btn = Gtk.Button()
        head_btn.add_css_class("flat")
        head_btn.add_css_class("section-button")
        head_lbl = Gtk.Label(label="Zariadenia", xalign=0)
        head_lbl.add_css_class("section-title")
        head_btn.set_child(head_lbl)
        head_btn.set_tooltip_text(ROOT_NAME)
        head_btn.connect("clicked", lambda _b: self.active.go_root())
        side_box.append(head_btn)

        self.side = Gtk.ListBox()
        self.side.add_css_class("navigation-sidebar")
        self.side.connect("row-activated", lambda _b, r: self.active.go_volume(r.volume))
        side_box.append(self.side)

        self.side_note = Gtk.Label(wrap=True, xalign=0)
        self.side_note.add_css_class("dim-label")
        self.side_note.set_margin_start(14)
        self.side_note.set_margin_end(12)
        self.side_note.set_visible(False)
        side_box.append(self.side_note)

        fav_head = Gtk.Label(label="Obľúbené", xalign=0)
        fav_head.add_css_class("section-title")
        fav_head.set_margin_top(18)
        fav_head.set_margin_start(14)
        side_box.append(fav_head)
        self.fav_side = Gtk.ListBox()
        self.fav_side.add_css_class("navigation-sidebar")
        self.fav_side.connect("row-activated", lambda _b, r: self.open_favorite(r.path))
        side_box.append(self.fav_side)
        self.fav_hint = Gtk.Label(label="Pravý klik na priečinok: Pridať medzi obľúbené", wrap=True, xalign=0)
        self.fav_hint.add_css_class("dim-label")
        self.fav_hint.set_margin_start(14)
        self.fav_hint.set_margin_end(12)
        side_box.append(self.fav_hint)

        body.append(side)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        body.append(right)

        self.panes = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, vexpand=True)
        self.panes.add_css_class("files-panes")
        right.append(self.panes)

        self.pane_a = Pane(self, self.volumes, self.prefs.get("view_a", "details"))
        self.pane_b = Pane(self, self.volumes, self.prefs.get("view_b", "details"))
        self.detail = Detail()
        self.panes.append(self.pane_a)
        self.panes.append(self.pane_b)
        self.panes.append(self.detail)

        right.append(self.function_bar())

        self.active = self.pane_a
        self.fill_sidebar()
        self.apply_mode()
        self.set_active(self.pane_a)

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self.on_key)
        self.add_controller(keys)

        # 1.11: zoznam zväzkov sa obnoví sám pri pripojení či odpojení disku
        self.storage = storage.Watcher(self.reload_volumes)
        self.storage_problem = self.storage.start() or ""
        if self.storage_problem:
            print("latte-files: automatické obnovenie diskov nefunguje:", self.storage_problem, file=sys.stderr)
        self.show_device_problems()
        self.connect("close-request", lambda *_a: (self.storage.stop(), False)[1])

    # ---------- nástroje ----------
    def open_path(self, path):
        """Otvorí priečinok (pri súbore jeho priečinok) v aktívnom paneli."""
        target = path if os.path.isdir(path) else os.path.dirname(path)
        found = vol_mod.locate(self.volumes, target)
        if found is None:
            self.notify("Cesta „%s“ nepatrí žiadnemu zväzku." % target)
            return
        volume, root = found
        self.active.open_location(volume, target, root)

    def update_title(self):
        active = getattr(self, "active", None)
        if active is not None:
            self.title_label.set_text(active.title_text())
            self.update_star()

    def update_star(self):
        active = self.active
        can = active.can_write() and active.path is not None
        self.btn_star.set_sensitive(can)
        starred = can and active.path in favorites.load()
        self.btn_star.set_icon_name("starred-symbolic" if starred else "non-starred-symbolic")
        self.btn_star.set_tooltip_text(
            "Odobrať z obľúbených" if starred else "Pridať aktuálny priečinok medzi obľúbené")

    def toggle_current_favorite(self):
        path = self.active.path
        if not self.active.can_write() or path is None:
            return
        if path in favorites.load():
            self.remove_favorite(path)
        else:
            self.add_favorite(path)

    def on_search(self, entry):
        text = entry.get_text()
        self.pane_a.set_filter(text)
        self.pane_b.set_filter(text)

    # ---------- zväzky ----------
    @staticmethod
    def signature(volumes):
        return [(v.key, v.path, v.name, v.size, v.removable, v.kind, v.state) for v in volumes]

    def show_device_problems(self):
        """Bez tichej degradácie: ak zoznam zariadení alebo sledovanie nefunguje, povie sa to v bočnom paneli."""
        parts = []
        if vol_mod.problem:
            parts.append("Zariadenia: " + vol_mod.problem)
        if self.storage_problem:
            parts.append("Disky sa neobnovujú samy: " + self.storage_problem)
        self.side_note.set_text("\n".join(parts))
        self.side_note.set_visible(bool(parts))

    def reload_volumes(self):
        fresh = vol_mod.list_volumes()
        self.show_device_problems()
        if self.signature(fresh) == self.signature(self.volumes):
            return                      # nič sa nezmenilo: nemazať výber v paneloch
        self.volumes[:] = fresh
        gone = [name for name in (self.pane_a.rebind(), self.pane_b.rebind()) if name]
        self.fill_sidebar()
        self.fill_favorites()
        self.refresh_all()
        if gone:
            self.notify("Zväzok „%s“ už nie je dostupný." % gone[0])

    def mount_volume(self, volume, then):
        def done(_mountpoint, err):
            if err:
                self.notify("Zväzok „%s“ sa nepodarilo pripojiť: %s" % (volume.name, err))
                return
            self.reload_volumes()
            for v in self.volumes:
                if v == volume and v.mounted:
                    then(v)
                    return
            self.notify("Zväzok „%s“ sa po pripojení nenašiel." % volume.name)

        storage.mount(volume.device, done)

    def unmount_volume(self, volume):
        def done(_res, err):
            if err:
                self.notify("Zväzok „%s“ sa nepodarilo odpojiť: %s" % (volume.name, err))
                return
            self.reload_volumes()

        storage.unmount(volume.device, done)

    # ---------- bočný panel ----------
    def fill_sidebar(self):
        clear_rows(self.side)
        for v in self.volumes:
            row = Gtk.ListBoxRow()
            row.volume = v
            line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            line.set_margin_start(10)
            line.set_margin_end(6)
            icon = Gtk.Image.new_from_icon_name(v.icon_name)
            icon.set_pixel_size(20)
            if not v.mounted:
                icon.add_css_class("dim-label")
            title = Gtk.Label(label=v.name, xalign=0, hexpand=True)
            title.set_ellipsize(3)
            line.append(icon)
            line.append(title)
            line.append(dim_label(v.size if v.mounted else (v.state_short or v.size), 1))
            row.set_tooltip_text(" · ".join(x for x in (v.kind_text, v.model, v.label, v.size, v.state_text) if x))
            if v.removable and v.mounted:
                eject = Gtk.Button(icon_name="media-eject-symbolic")
                eject.add_css_class("flat")
                eject.add_css_class("eject")
                eject.set_tooltip_text("Odpojiť")
                eject.connect("clicked", lambda _b, vol=v: self.unmount_volume(vol))
                line.append(eject)
            row.set_child(line)
            self.attach_volume_menu(row, v)
            self.side.append(row)
        self.fill_favorites()

    def fill_favorites(self):
        clear_rows(self.fav_side)
        paths = favorites.load()
        self.fav_hint.set_visible(not paths)
        for path in paths:
            row = Gtk.ListBoxRow()
            row.path = path
            line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            line.set_margin_start(10)
            line.set_margin_end(10)
            found = vol_mod.locate(self.volumes, path) if os.path.isdir(path) else None
            icon = Gtk.Image.new_from_icon_name("folder")
            icon.set_pixel_size(20)
            title = Gtk.Label(label=os.path.basename(path) or path, xalign=0, hexpand=True)
            title.set_ellipsize(3)
            line.append(icon)
            line.append(title)
            line.append(dim_label(found[0].name if found else "nedostupné", 1))
            if not found:
                title.add_css_class("dim-label")
                icon.add_css_class("dim-label")
            row.set_child(line)
            gesture = Gtk.GestureClick()
            gesture.set_button(3)
            gesture.connect(
                "pressed",
                lambda _g, _n, x, y, r=row, p=path: popup_menu(
                    r, [[("Odobrať z obľúbených", lambda: self.remove_favorite(p))]], x, y))
            row.add_controller(gesture)
            self.fav_side.append(row)
        self.update_star()

    def add_favorite(self, path):
        if vol_mod.locate(self.volumes, path) is None:
            self.notify("Tento priečinok sa nedá pridať medzi obľúbené.")
            return
        favorites.add(path)
        self.fill_favorites()

    def remove_favorite(self, path):
        favorites.remove(path)
        self.fill_favorites()

    def open_favorite(self, path):
        found = vol_mod.locate(self.volumes, path) if os.path.isdir(path) else None
        if found is None:
            self.notify("Priečinok „%s“ nie je dostupný. Možno je zväzok odpojený alebo priečinok zmizol. "
                        "Z obľúbených ho odoberiete pravým klikom." % (os.path.basename(path) or path))
            return
        self.active.open_location(found[0], path, found[1])

    def attach_volume_menu(self, widget, volume):
        gesture = Gtk.GestureClick()
        gesture.set_button(3)
        gesture.connect("pressed", lambda _g, _n, x, y, w=widget, v=volume: self.volume_menu(w, v, x, y))
        widget.add_controller(gesture)

    def volume_menu(self, widget, volume, x, y):
        if not volume.removable:
            self.ask_rename_volume(volume)      # pevný zväzok: rovno premenovanie
            return
        groups = [[("Premenovať", lambda: self.ask_rename_volume(volume))]]
        if volume.mounted:
            groups.append([("Odpojiť", lambda: self.unmount_volume(volume))])
        elif volume.mountable:
            groups.append([("Pripojiť", lambda: self.mount_volume(volume, lambda _v: None))])
        popup_menu(widget, groups, x, y)

    def sync_sidebar(self):
        """Zvýrazní v bočnom paneli zväzok, v ktorom je aktívny panel."""
        vol = self.active.volume
        self.side.unselect_all()
        if vol is None:
            return
        row = self.side.get_first_child()
        while row is not None:
            if isinstance(row, Gtk.ListBoxRow) and getattr(row, "volume", None) == vol:
                self.side.select_row(row)
                break
            row = row.get_next_sibling()

    # ---------- režimy ----------
    def cycle_mode(self, _btn=None):
        order = [m for m, _i, _t in MODES]
        self.set_mode(order[(order.index(self.mode) + 1) % len(order)])

    def set_mode(self, mode):
        if mode == self.mode and getattr(self, "_mode_applied", False):
            return
        self.mode = mode
        self.apply_mode()

    def apply_mode(self):
        self._mode_applied = True
        for mode, btn in self.mode_buttons.items():
            if btn.get_active() != (mode == self.mode):
                btn.set_active(mode == self.mode)
        self.pane_b.set_visible(self.mode != "simple")
        self.detail.set_visible(self.mode == "simple")
        self.pane_a.refresh()
        self.pane_b.refresh()

    def set_view_style(self, style):
        """Štýl zobrazenia aktívneho panela (druhý panel si drží vlastný)."""
        self.active.set_view_style(style)

    def on_view_style_changed(self, pane):
        key = "view_a" if pane is self.pane_a else "view_b"
        self.prefs[key] = pane.view_style
        try:
            prefs.update("files", **{key: pane.view_style})
        except OSError as err:
            print("latte-files: nastavenie zobrazenia sa nepodarilo uložiť:", err, file=sys.stderr)
        if pane is self.active:
            self.update_view_button()

    def update_view_button(self):
        style = self.active.view_style
        for vid, icon, title, _hint in VIEWS:
            if vid == style:
                self.view_button.set_icon_name(icon)
                self.view_button.set_tooltip_text("Zobrazenie: %s (Ctrl+1 až Ctrl+4)" % title)
            self.view_checks[vid].set_opacity(1.0 if vid == style else 0.0)

    def set_active(self, pane):
        self.active = pane
        self.pane_a.remove_css_class("active")
        self.pane_b.remove_css_class("active")
        pane.add_css_class("active")
        self.update_title()
        self.update_view_button()
        self.sync_sidebar()
        self.update_detail()

    def other(self):
        return self.pane_b if self.active is self.pane_a else self.pane_a

    def update_detail(self):
        detail = getattr(self, "detail", None)
        if detail is None or self.mode != "simple":
            return
        active = getattr(self, "active", None)
        detail.show_items(active.detail_items() if active is not None else [])

    # ---------- spodná lišta ----------
    def function_bar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bar.add_css_class("function-bar")
        items = [
            ("F2 Premenovať", self.do_rename),
            ("F5 Kopírovať", self.do_copy),
            ("F6 Presunúť", self.do_move),
            ("F7 Priečinok", self.do_mkdir),
            ("F8 Do koša", self.do_trash),
        ]
        for label, action in items:
            btn = Gtk.Button(label=label)
            btn.add_css_class("flat")
            btn.set_hexpand(True)
            btn.connect("clicked", lambda _b, a=action: a())
            bar.append(btn)
        return bar

    # ---------- dialógy ----------
    def ask_text(self, title, initial, on_ok):
        dlg = Gtk.Window(transient_for=self, modal=True, title=title)
        dlg.set_default_size(360, -1)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        for f in (box.set_margin_top, box.set_margin_bottom, box.set_margin_start, box.set_margin_end):
            f(18)
        entry = Gtk.Entry(text=initial)
        box.append(entry)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, halign=Gtk.Align.END)
        cancel = Gtk.Button(label="Zrušiť")
        cancel.connect("clicked", lambda _b: dlg.destroy())
        ok = Gtk.Button(label="Potvrdiť")
        ok.add_css_class("suggested-action")

        def apply(*_a):
            text = entry.get_text().strip()
            dlg.destroy()
            if text:
                on_ok(text)

        ok.connect("clicked", apply)
        entry.connect("activate", apply)
        row.append(cancel)
        row.append(ok)
        box.append(row)
        dlg.set_child(box)
        dlg.present()

    def ask_choice(self, text, choices, on_choice, title="Potvrdenie"):
        """choices = [(text tlačidla, hodnota, css trieda alebo None)]; zavretie okna = nič."""
        dlg = Gtk.Window(transient_for=self, modal=True, title=title)
        dlg.set_default_size(420, -1)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        for f in (box.set_margin_top, box.set_margin_bottom, box.set_margin_start, box.set_margin_end):
            f(18)
        box.append(Gtk.Label(label=text, wrap=True, xalign=0))
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, halign=Gtk.Align.END)
        for label, value, css in choices:
            btn = Gtk.Button(label=label)
            if css:
                btn.add_css_class(css)
            btn.connect("clicked", lambda _b, v=value: (dlg.destroy(), on_choice(v)))
            row.append(btn)
        box.append(row)
        dlg.set_child(box)
        dlg.present()

    def ask_confirm(self, text, on_ok, ok_label="Pokračovať"):
        self.ask_choice(
            text,
            [("Zrušiť", None, None), (ok_label, True, "destructive-action")],
            lambda v: on_ok() if v else None,
        )

    def notify(self, text):
        dlg = Gtk.AlertDialog()
        dlg.set_message(text)
        dlg.show(self)

    # ---------- práca ako správca ----------
    def offer_admin(self, text, run):
        """Operácia zlyhala pre práva: ponúkne zopakovanie ako správca (polkit)."""
        if not jobs.admin_available():
            self.notify(text + "\n\nSprávcovský pomocník nie je nainštalovaný (tools/install-admin.sh).")
            return
        self.ask_choice(
            text + "\n\nZopakovať ako správca?",
            [("Zrušiť", None, None), ("Ako správca", True, "suggested-action")],
            lambda ok: run() if ok else None,
            title="Prístup odmietnutý",
        )

    def admin_call(self, args):
        def done(res):
            if res.get("state") == "error":
                err = res.get("error") or ["", 0, "neznáma chyba"]
                self.notify("Operácia ako správca zlyhala: %s" % err[2])
            self.refresh_all()

        jobs.call(args, done)

    # ---------- operácie ----------
    def open_object(self, path):
        try:
            gfile = Gio.File.new_for_path(path)
            info = gfile.query_info("standard::content-type", 0, None)
            ctype = info.get_content_type()
            app = Gio.AppInfo.get_default_for_type(ctype, False) if ctype else None
            if app is None:
                self.notify("Pre tento typ súboru nie je nastavená aplikácia.")
                return
            app.launch([gfile], None)
        except GLib.Error as err:
            self.notify("Súbor sa nepodarilo otvoriť: " + err.message)

    def refresh_all(self):
        self.pane_a.refresh()
        self.pane_b.refresh()

    def do_mkdir(self):
        if not self.active.can_write():
            return
        parent = self.active.path

        def create(name):
            try:
                os.mkdir(os.path.join(parent, name))
                self.refresh_all()
            except PermissionError:
                self.offer_admin("Priečinok sa nepodarilo vytvoriť: prístup odmietnutý.",
                                 lambda: self.admin_call(["mkdir", parent, name]))
            except OSError as err:
                self.notify("Priečinok sa nepodarilo vytvoriť: " + (err.strerror or str(err)))

        self.ask_text("Nový priečinok", "", create)

    def do_rename(self):
        sel = self.active.selection()
        if len(sel) > 1:
            self.notify("Premenovať sa dá naraz len jedna položka.")
            return
        if not sel:
            return
        src = sel[0]

        def rename(name):
            dst = os.path.join(os.path.dirname(src), name)
            if os.path.lexists(dst):
                self.notify("Položka s menom „%s“ už existuje." % name)
                return
            try:
                os.rename(src, dst)
                self.refresh_all()
            except PermissionError:
                self.offer_admin("Premenovanie zlyhalo: prístup odmietnutý.",
                                 lambda: self.admin_call(["rename", src, name]))
            except OSError as err:
                self.notify("Premenovanie zlyhalo: " + (err.strerror or str(err)))

        self.ask_text("Premenovať", os.path.basename(src), rename)

    def transfer(self, kind):
        sources = self.active.selection()
        if not sources:
            return
        target_pane = self.other()
        if self.mode == "simple" or not target_pane.can_write():
            self.notify("Cieľ nie je určený. Prepnite na dvojpanel.")
            return
        dest = target_pane.path
        word = "Presunúť" if kind == "move" else "Kopírovať"
        what = ("„%s“" % os.path.basename(sources[0])) if len(sources) == 1 else \
            count_text(len(sources), "položku", "položky", "položiek")

        def proceed():
            found = fileops.conflicts(sources, dest)
            if not found:
                self.start_transfer(kind, sources, dest, fileops.KEEP_BOTH)
                return
            self.ask_conflict(found, lambda policy: self.start_transfer(kind, sources, dest, policy))

        self.ask_confirm("%s %s do %s?" % (word, what, dest), proceed)

    def ask_conflict(self, found, on_policy):
        names = [os.path.basename(dst) for _src, dst in found]
        shown = ", ".join("„%s“" % n for n in names[:3])
        if len(names) > 3:
            shown += " a %d ďalších" % (len(names) - 3)
        text = "V cieli už existuje: %s." % shown
        choices = [
            ("Zrušiť", None, None),
            ("Preskočiť", fileops.SKIP, None),
            ("Ponechať obe", fileops.KEEP_BOTH, "suggested-action"),
        ]
        if not any(os.path.isdir(dst) for _src, dst in found):
            choices.append(("Nahradiť", fileops.REPLACE, "destructive-action"))
        else:
            text += " Priečinky sa neprepisujú."
        self.ask_choice(text, choices, lambda p: on_policy(p) if p else None, title="Položka už existuje")

    def start_transfer(self, kind, sources, dest, policy, admin=False):
        if admin:
            job = jobs.AdminJob(kind, sources, dest, policy)
        else:
            job = jobs.LocalJob(fileops.Transfer(kind, sources, dest, policy))
        title = "Presúvanie" if kind == "move" else "Kopírovanie"
        word = "Presun" if kind == "move" else "Kopírovanie"

        def finished(result):
            if result.state != "error":
                return
            path, code, message = result.error
            left = [s for s in sources if s not in result.done]
            if not admin and code in DENIED:
                self.offer_admin("%s zlyhalo: prístup odmietnutý (%s)." % (word, path),
                                 lambda: self.start_transfer(kind, left, dest, policy, admin=True))
                return
            text = "%s zlyhalo: %s (%s)." % (word, message, path)
            if result.done:
                text += " Hotových je %d z %d." % (len(result.done), len(sources))
            self.notify(text)

        self.run_job(title, job, finished)

    def run_job(self, title, job, on_finished):
        dlg = ProgressDialog(self, title, job.cancel)
        timer = {"id": 0}
        timer["id"] = GLib.timeout_add(PROGRESS_AFTER_MS, self._reveal, dlg, timer)

        def done(result):
            if timer["id"]:
                GLib.source_remove(timer["id"])
            dlg.destroy()
            self.refresh_all()
            on_finished(result)

        job.start(dlg.update, done)

    @staticmethod
    def _reveal(dlg, timer):
        timer["id"] = 0
        dlg.present()
        return False

    def do_copy(self):
        self.transfer("copy")

    def do_move(self):
        self.transfer("move")

    def do_trash(self):
        sources = self.active.selection()
        if not sources:
            return
        what = ("„%s“" % os.path.basename(sources[0])) if len(sources) == 1 else \
            count_text(len(sources), "položku", "položky", "položiek")

        def run():
            failed = []
            for src in sources:
                try:
                    Gio.File.new_for_path(src).trash(None)
                except GLib.Error as err:
                    failed.append((src, err))
            self.refresh_all()
            if failed:
                self.trash_failed(failed)

        self.ask_confirm("Presunúť %s do Koša?" % what, run)

    def trash_failed(self, failed):
        paths = [p for p, _e in failed]
        quark = Gio.io_error_quark()

        def kind(err):
            if err.matches(quark, Gio.IOErrorEnum.PERMISSION_DENIED):
                return "denied"
            if err.matches(quark, Gio.IOErrorEnum.NOT_SUPPORTED):
                return "no-trash"
            return "other"

        kinds = {kind(e) for _p, e in failed}
        if kinds == {"denied"}:
            if not jobs.admin_available():
                self.notify("Do Koša sa nedá presunúť: prístup odmietnutý.\n\n"
                            "Správcovský pomocník nie je nainštalovaný (tools/install-admin.sh).")
                return
            self.ask_confirm(
                "Do Koša sa nedá presunúť: prístup odmietnutý.\n\nOdstrániť natrvalo ako správca? "
                "Nedá sa to vrátiť späť.",
                lambda: self.admin_call(["delete", *paths]), ok_label="Odstrániť natrvalo")
        elif kinds == {"no-trash"}:
            def delete_here():
                for path in paths:
                    try:
                        fileops.remove_tree(path)
                    except OSError as err:
                        self.notify("Odstránenie zlyhalo: %s (%s)" % (err.strerror, path))
                        break
                self.refresh_all()

            self.ask_confirm("Na tomto zväzku nie je Kôš. Odstrániť natrvalo? Nedá sa to vrátiť späť.",
                             delete_here, ok_label="Odstrániť natrvalo")
        else:
            self.notify("Do Koša sa nepodarilo presunúť: %s (%s)" % (failed[0][1].message, failed[0][0]))

    def ask_rename_volume(self, volume):
        def apply(name):
            if vol_mod.rename(volume, name):
                self.fill_sidebar()
                self.refresh_all()

        self.ask_text("Premenovať zväzok", volume.name, apply)

    # ---------- klávesnica ----------
    def on_key(self, _c, keyval, _code, state):
        ctrl = state & Gdk.ModifierType.CONTROL_MASK
        if keyval == Gdk.KEY_Tab and self.mode != "simple":
            self.set_active(self.other())
            return True
        if ctrl and keyval in (Gdk.KEY_a, Gdk.KEY_A):
            self.active.list.select_all()
            return True
        if ctrl and Gdk.KEY_1 <= keyval <= Gdk.KEY_4:
            self.set_view_style(VIEW_IDS[keyval - Gdk.KEY_1])
            return True
        if ctrl and keyval in (Gdk.KEY_f, Gdk.KEY_F):
            self.search.grab_focus()
            return True
        if keyval == Gdk.KEY_F2:
            self.do_rename()
            return True
        if keyval == Gdk.KEY_F5:
            self.do_copy()
            return True
        if keyval == Gdk.KEY_F6:
            self.do_move()
            return True
        if keyval == Gdk.KEY_F7:
            self.do_mkdir()
            return True
        if keyval in (Gdk.KEY_F8, Gdk.KEY_Delete):
            self.do_trash()
            return True
        if keyval == Gdk.KEY_BackSpace:
            self.active.up()
            return True
        return False


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.latteos.Files",
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)

    def do_activate(self):
        win = Window(self)
        theme.load(win.get_display())
        win.present()

    def do_open(self, files, _n_files, _hint):
        """latte-files CESTA: okno hneď v danom priečinku (napr. z hľadania v prompte lišty)."""
        for file in files:
            win = Window(self)
            theme.load(win.get_display())
            win.open_path(file.get_path())
            win.present()


if __name__ == "__main__":
    App().run(sys.argv)
