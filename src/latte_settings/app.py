#!/usr/bin/env python3
"""latte-settings: Nastavenia systému LatteOS.

Vzhľad a rozloženie vychádzajú zo správcu súborov (ForkLift): pruh nástrojov, priehľadnejší bočný
panel, panel obsahu s karamelovou čiarou hore a inšpektor vpravo. Bočný panel nesie päť vrstvených
kariet oblastí (Softvér, Dáta, Hardvér, Účet, Prostredie) a pod nimi menšiu kartu Systém;
podľa návrhu main_setting_v2.md. Aktívna karta sa rozbalí na svoje stránky, ostatné ostanú
viditeľné ako „chrbát“ s ikonou, názvom a stavom. Hlavné karty sa neposúvajú, posúva sa len
zoznam stránok vnútri aktívnej karty.

Spustenie: latte-settings [settings://oblasť/stránka | oblasť | stránka]
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib, Gdk  # noqa: E402

from latte_common import prefs, settings, theme  # noqa: E402
from latte_settings import display, model, pages  # noqa: E402

FILES_APP = os.path.join(os.path.dirname(__file__), "..", "latte_files", "app.py")
NOTICE_MS = 6000
CARD_MS = 200                   # krátka a pokojná animácia rozbalenia karty (kap. 9)
PREFS = "settings"              # ~/.config/latteos/settings.toml: nedávne stránky


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


class AreaCard(Gtk.Box):
    """Karta oblasti: zbalená je „chrbát“ (ikona, názov, stav), aktívna ukáže zoznam svojich stránok."""

    def __init__(self, window, gid, title, page_list=(), compact=False):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.window = window
        self.gid = gid
        self.title = title
        self.rows = {}
        self.expanded = False
        self.add_css_class("area-card")
        if compact:
            self.add_css_class("compact")

        self.head = Gtk.Button()
        self.head.add_css_class("flat")
        self.head.add_css_class("area-head")
        line = Gtk.Box(spacing=10)
        icon = Gtk.Image.new_from_icon_name(pages.AREA_ICONS[gid])
        icon.set_pixel_size(18)
        line.append(icon)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1, hexpand=True)
        text.set_valign(Gtk.Align.CENTER)
        name = Gtk.Label(label=title.upper(), xalign=0)
        name.add_css_class("area-title")
        self.summary = Gtk.Label(xalign=0, ellipsize=3)
        self.summary.add_css_class("area-summary")
        text.append(name)
        text.append(self.summary)
        line.append(text)
        self.glyph_box = Gtk.Box()
        line.append(self.glyph_box)
        self.chevron = Gtk.Image.new_from_icon_name("pan-end-symbolic")
        line.append(self.chevron)
        self.head.set_child(line)
        self.head.connect("clicked", lambda _b: self.on_head())
        self.append(self.head)

        self.revealer = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN,
                                     transition_duration=CARD_MS)
        self.list = Gtk.ListBox()
        self.list.add_css_class("navigation-sidebar")
        self.list.add_css_class("area-pages")
        self.list.connect("row-activated", lambda _b, row: window.show_page(row.page))
        for page in page_list:
            row = Gtk.ListBoxRow()
            row.page = page
            line = Gtk.Box(spacing=10)
            image = Gtk.Image.new_from_icon_name(page.icon or "emblem-system-symbolic")
            if page.status == "planned":
                image.add_css_class("dim-label")
            line.append(image)
            title_label = Gtk.Label(label=page.title, xalign=0, hexpand=True, ellipsize=3)
            if page.status == "planned":
                title_label.add_css_class("dim-label")       # plánované: vidieť, ale tlmene
            line.append(title_label)
            row.set_child(line)
            self.list.append(row)
            self.rows[page.id] = row
        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, propagate_natural_height=True)
        scroll.set_child(self.list)
        self.revealer.set_child(scroll)
        self.append(self.revealer)
        self.set_active(False)

    def on_head(self):
        """Šípka a hlavička rozbalia kartu; ďalší klik ju zbalí do pôvodného stavu (obsah vpravo ostane)."""
        if self.gid == "home":
            self.window.show_home()
        elif self.expanded:
            self.set_active(False)
        elif self.window.current_group() == self.gid:
            self.set_active(True)               # stránka tejto oblasti je otvorená, len sa ukáže jej zoznam
        else:
            self.window.show_area(self.gid)

    def set_status(self, status):
        self.summary.set_text(status.summary)
        child = self.glyph_box.get_first_child()
        if child is not None:
            self.glyph_box.remove(child)
        self.glyph_box.append(pages.state_label(status.state))
        # čítačka obrazovky dostane celý význam karty, nie len jej názov
        self.head.update_property([Gtk.AccessibleProperty.LABEL], [
            "%s, %s: %s" % (self.title, model.state_text(status.state), status.summary)])

    def set_active(self, active):
        self.expanded = active and bool(self.rows)
        if self.rows:
            self.head.update_state([Gtk.AccessibleState.EXPANDED], [int(self.expanded)])
        if active:
            self.add_css_class("active")
        else:
            self.remove_css_class("active")
        self.chevron.set_from_icon_name("pan-down-symbolic" if active else "pan-end-symbolic")
        self.chevron.set_visible(self.gid != "home")
        self.revealer.set_reveal_child(active and bool(self.rows))

    def select_page(self, page_id):
        row = self.rows.get(page_id)
        if row is None:
            self.list.unselect_all()
        else:
            self.list.select_row(row)


class Window(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Nastavenia")
        self.add_css_class("latte-settings")
        self.set_default_size(1240, 760)
        self.registry = settings.Registry()
        self.stores = {}
        self.facts = model.gather_facts(self.registry)
        self.statuses = model.area_statuses(self.registry, self.facts)
        self.recent = model.recent_parse(prefs.load(PREFS).get("recent", ""))
        self.index = None
        self.view = None
        self.clearing = False           # vymazanie hľadania z kódu nemá prekresliť starú stránku
        self.location = ("home", None)
        self.history = [self.location]
        self.position = 0
        self.notice_source = 0
        self.pending = None             # potvrdenie zmeny (obrazovka): {"left", "source", "keep", "revert", "text"}

        # ---- pruh nástrojov (ako vo ForkLifte: navigácia, názov, hľadanie)
        header = Gtk.HeaderBar()
        header.add_css_class("files-toolbar")
        header.add_css_class("latte-titlebar")
        self.set_titlebar(header)
        self.btn_back = tool_button("go-previous-symbolic", "Späť (Alt+←)", lambda: self.go_history(-1))
        self.btn_fwd = tool_button("go-next-symbolic", "Dopredu (Alt+→)", lambda: self.go_history(1))
        header.pack_start(linked(self.btn_back, self.btn_fwd))
        self.title_label = Gtk.Label(label="Nastavenia")
        self.title_label.add_css_class("toolbar-title")
        header.set_title_widget(self.title_label)
        self.search = Gtk.SearchEntry(placeholder_text="Hľadať nastavenie")
        self.search.set_size_request(240, -1)
        self.search.connect("search-changed", self.on_search)
        self.search.connect("activate", self.open_first_hit)
        self.search.connect("stop-search", lambda e: e.set_text(""))
        header.pack_end(self.search)

        # ---- telo: karty oblastí | obsah | inšpektor
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(body)

        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        side.add_css_class("files-sidebar")
        side.set_size_request(280, -1)
        side.set_hexpand(False)                 # inak ho roztiahne hexpand vnútorných prvkov
        self.cards = {}
        self.home_card = AreaCard(self, "home", "Domov", compact=True)
        side.append(self.home_card)
        for gid, title in self.registry.groups.items():
            if gid == "system":
                continue
            card = AreaCard(self, gid, title, self.registry.area_pages(gid))
            self.cards[gid] = card
            side.append(card)
        filler = Gtk.Box(vexpand=True)          # Systém drží pri spodnom okraji, nie je šiesta hlavná karta (kap. 4)
        side.append(filler)
        system = AreaCard(self, "system", self.registry.groups["system"], self.registry.area_pages("system"), compact=True)
        self.cards["system"] = system
        side.append(system)
        body.append(side)
        for gid, card in self.cards.items():
            card.set_status(self.statuses[gid])
        self.home_card.set_status(model.Status(self.overall_state(), "Stav systému"))

        pane = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        pane.add_css_class("pane")
        pane.add_css_class("active")
        active_bar = Gtk.Box()
        active_bar.add_css_class("active-bar")
        pane.append(active_bar)
        self.notice_revealer = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.notice_label = Gtk.Label(xalign=0, wrap=True)
        self.notice_label.add_css_class("notice")
        self.notice_revealer.set_child(self.notice_label)
        pane.append(self.notice_revealer)
        pane.append(self.build_confirm_bar())
        self.holder = Gtk.Box(hexpand=True, vexpand=True)
        pane.append(self.holder)
        body.append(pane)

        self.inspector = pages.Inspector(self)
        self.inspector.set_visible(False)
        self.inspector.set_hexpand(False)
        body.append(self.inspector)

        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self.on_key)
        self.add_controller(keys)
        self.connect("close-request", self.on_close_request)
        self.show_location(self.location, record=False)

    # ---------- zdieľané veci pre stránky ----------
    def store(self, domain_id):
        if domain_id not in self.stores:
            self.stores[domain_id] = self.registry.store(domain_id)
        return self.stores[domain_id]

    def current_group(self):
        """Oblasť aktuálne otvorenej stránky alebo prehľadu (None na Domove)."""
        kind, ident = self.location
        if kind == "page":
            return self.registry.page(ident).group
        return ident if kind == "area" else None

    def overall_state(self):
        states = [s.state for s in self.statuses.values()]
        for state in ("problem", "attention", "busy"):
            if state in states:
                return state
        return "ok"

    def notify(self, text):
        self.notice_label.set_text(text)
        self.notice_revealer.set_reveal_child(True)
        if self.notice_source:
            GLib.source_remove(self.notice_source)
        self.notice_source = GLib.timeout_add(NOTICE_MS, self.hide_notice)

    def hide_notice(self):
        self.notice_source = 0
        self.notice_revealer.set_reveal_child(False)
        return False

    # ---------- potvrdenie zmeny (napr. rozlíšenia): bez potvrdenia sa vráti ----------
    def build_confirm_bar(self):
        self.confirm_revealer = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN)
        bar = Gtk.Box(spacing=10)
        bar.add_css_class("notice")
        self.confirm_label = Gtk.Label(xalign=0, wrap=True, hexpand=True)
        bar.append(self.confirm_label)
        keep = Gtk.Button(label="Ponechať")
        keep.add_css_class("suggested-action")
        keep.connect("clicked", lambda _b: self.resolve_confirm(True))
        back = Gtk.Button(label="Vrátiť")
        back.connect("clicked", lambda _b: self.resolve_confirm(False))
        bar.append(keep)
        bar.append(back)
        self.confirm_revealer.set_child(bar)
        return self.confirm_revealer

    def confirm_pending(self):
        return self.pending is not None

    def ask_keep(self, text, seconds, on_keep, on_revert):
        """Ukáže „Ponechať toto nastavenie?“ s odpočtom; po uplynutí (alebo pri zatvorení okna) sa zavolá on_revert."""
        self.pending = {"left": seconds, "keep": on_keep, "revert": on_revert, "text": text, "source": 0}
        self.update_confirm_label()
        self.confirm_revealer.set_reveal_child(True)
        self.pending["source"] = GLib.timeout_add_seconds(1, self.confirm_tick)

    def update_confirm_label(self):
        self.confirm_label.set_text("%s Ponechať toto nastavenie? (Enter = áno, Esc = vrátiť) Vráti sa o %d s." % (
            self.pending["text"], self.pending["left"]))

    def confirm_tick(self):
        if self.pending is None:
            return False
        self.pending["left"] -= 1
        if self.pending["left"] <= 0:
            self.pending["source"] = 0
            self.resolve_confirm(False)
            return False
        self.update_confirm_label()
        return True

    def resolve_confirm(self, keep):
        pending, self.pending = self.pending, None
        if pending is None:
            return
        if pending["source"]:
            GLib.source_remove(pending["source"])
        self.confirm_revealer.set_reveal_child(False)
        pending["keep" if keep else "revert"]()

    def on_close_request(self, *_args):
        self.resolve_confirm(False)             # nepotvrdená zmena sa nesmie ponechať
        return False

    def launch_files(self):
        """Správca súborov: prehliadanie a manipulácia so súbormi nie je vec Nastavení."""
        try:
            subprocess.Popen([sys.executable, os.path.abspath(FILES_APP)])
        except OSError as err:
            self.notify("Správcu súborov sa nepodarilo spustiť: %s" % (err.strerror or err))

    # ---------- navigácia ----------
    def show_home(self):
        self.show_location(("home", None))

    def show_area(self, gid):
        self.show_location(("area", gid))

    def show_page(self, page, focus_key=None, obj=""):
        self.show_location(("page", page.id), focus_key=focus_key, obj=obj)

    def open_target(self, target):
        """Odkaz z príkazového riadka: settings://oblasť/stránka."""
        target, obj = self.registry.split_object(target)
        found = self.registry.resolve(target)
        if found is None:
            self.notify("V Nastaveniach nie je miesto „%s“." % target)
            return
        self.clear_search()
        if found[0] == "page":
            self.show_page(found[1], obj=obj)
        else:
            self.show_area(found[1])

    def open_hit(self, hit):
        self.clear_search()
        self.show_page(hit.page, focus_key=hit.key.id if hit.key else None)

    def go_history(self, step):
        target = self.position + step
        if 0 <= target < len(self.history):
            self.position = target
            self.show_location(self.history[target], record=False)

    def clear_search(self):
        self.clearing = True
        try:
            self.search.set_text("")
        finally:
            self.clearing = False
        self.index = None                           # ďalšie hľadanie vidí aktuálne hodnoty

    def show_location(self, location, record=True, focus_key=None, obj=""):
        self.clear_search()
        kind, ident = location
        if self.view is not None:
            self.view.cleanup()
        page = None
        if kind == "page":
            page = self.registry.page(ident)
            view, title = self.build_page(page, obj), page.title
        elif kind == "area":
            view, title = pages.AreaView(self, ident), self.registry.groups[ident]
        else:
            view, title = pages.HomeView(self), "Nastavenia"
        self.set_view(view)
        self.title_label.set_text(title)
        self.location = location
        if record and location != self.history[self.position]:
            self.history = self.history[:self.position + 1] + [location]
            self.position = len(self.history) - 1
        self.btn_back.set_sensitive(self.position > 0)
        self.btn_fwd.set_sensitive(self.position < len(self.history) - 1)

        active = page.group if page else (ident if kind == "area" else None)
        self.home_card.set_active(kind == "home")
        for gid, card in self.cards.items():
            card.set_active(gid == active)
            card.select_page(page.id if page and gid == active else None)
        if page is not None:
            self.inspector.show_page(page)
            self.remember(page)
        self.inspector.set_visible(page is not None)
        if focus_key and page is not None:
            self.view.focus_key(focus_key)

    def build_page(self, page, obj=""):
        if page.view == "display":
            return display.DisplayView(self, page, obj)
        if page.view == "about":
            return pages.AboutView(self, page)
        if page.view == "storage":
            return pages.StorageView(self, page)
        if page.domain:
            return pages.SchemaView(self, page)
        return pages.PlannedView(self, page)

    def set_view(self, view):
        child = self.holder.get_first_child()
        if child is not None:
            self.holder.remove(child)
        self.holder.append(view.widget)
        self.view = view

    def remember(self, page):
        self.recent = model.recent_add(self.recent, page.id)
        try:
            prefs.update(PREFS, recent=",".join(self.recent))
        except OSError as err:
            print("latte-settings: nedávne stránky sa nepodarilo uložiť:", err, file=sys.stderr)

    # ---------- hľadanie ----------
    def hits(self, query):
        if self.index is None:
            self.index = model.build_index(
                self.registry, lambda page, key: self.store(page.domain).get(key.id) if page.domain else None)
        return model.search(self.index, query)

    def on_search(self, entry):
        if self.clearing:
            return
        query = entry.get_text().strip()
        if not query:
            self.show_location(self.location, record=False)
            return
        if self.view is not None:
            self.view.cleanup()
        self.set_view(pages.ResultsView(self, self.hits(query), query))
        self.title_label.set_text("Hľadanie")
        self.inspector.set_visible(False)
        for card in self.cards.values():
            card.set_active(False)
        self.home_card.set_active(False)

    def open_first_hit(self, entry):
        query = entry.get_text().strip()
        hits = self.hits(query) if query else []
        if hits:
            self.open_hit(hits[0])

    def on_key(self, _ctrl, keyval, _code, state):
        if self.pending is not None and keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_Escape):
            self.resolve_confirm(keyval != Gdk.KEY_Escape)          # Enter ponechá, Esc vráti
            return True
        ctrl = state & Gdk.ModifierType.CONTROL_MASK
        alt = state & Gdk.ModifierType.ALT_MASK
        if ctrl and keyval in (Gdk.KEY_f, Gdk.KEY_F):
            self.search.grab_focus()
            return True
        if alt and keyval == Gdk.KEY_Left:
            self.go_history(-1)
            return True
        if alt and keyval == Gdk.KEY_Right:
            self.go_history(1)
            return True
        return False


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.latteos.Settings",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.window = None

    def do_command_line(self, cmdline):
        if self.window is None:
            self.window = Window(self)
            theme.load(self.window.get_display())
        args = cmdline.get_arguments()[1:]
        if args:
            self.window.open_target(args[0])
        self.window.present()
        return 0


if __name__ == "__main__":
    sys.exit(App().run(sys.argv))
