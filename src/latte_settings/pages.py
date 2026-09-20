"""Obsah okna Nastavení: domov, prehľad oblasti, stránky zo schém, plánované stránky, O LatteOS,
Úložisko, výsledky hľadania a inšpektor vpravo.

Každá stránka má rovnakú stavbu (main_setting_v2.md, kap. 74): názov, krátke vysvetlenie,
hlavná konfigurácia, stav a odkaz na špecializovaného správcu. Nastavenia nevlastnia operácie:
kde ich vlastní iný správca, stránka ukáže stav a tlačidlo, nie vlastnú implementáciu.
"""
import os
import platform

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib  # noqa: E402

from latte_common import build, paths, settings  # noqa: E402
from latte_common import volumes as vol_mod  # noqa: E402
from latte_settings import model  # noqa: E402
from latte_settings.controls import KeyRow  # noqa: E402

AREA_ICONS = {
    "home": "go-home-symbolic",
    "software": "view-grid-symbolic",
    "data": "folder-symbolic",
    "hardware": "computer-symbolic",
    "account": "avatar-default-symbolic",
    "environment": "preferences-desktop-appearance-symbolic",
    "system": "emblem-system-symbolic",
}
MANAGER_NAMES = {"files": "Správca súborov"}


# ---------------------------------------------------------------- stavebné kamene
def label(text, css=None, xalign=0.0, wrap=True, selectable=False):
    lbl = Gtk.Label(label=text, xalign=xalign, wrap=wrap, selectable=selectable)
    if css:
        for name in css.split():
            lbl.add_css_class(name)
    return lbl


def group_title(text):
    lbl = label(text.upper(), "section-title")
    lbl.set_margin_top(20)
    lbl.set_margin_bottom(6)
    lbl.set_margin_start(4)
    return lbl


def settings_group(children):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    box.add_css_class("settings-group")
    for child in children:
        box.append(child)
    return box


def info_row(title, value, mono=False):
    row = Gtk.Box(spacing=16)
    row.add_css_class("settings-row")
    row.append(label(title, "row-title", wrap=False))
    row.get_last_child().set_hexpand(True)
    row.append(label(value or "–", "mono" if mono else "row-note", xalign=1.0, selectable=True))
    return row


def notice(text, danger=False):
    box = Gtk.Box(spacing=8)
    box.add_css_class("notice")
    if danger:
        box.add_css_class("danger")
    box.append(label(text, xalign=0.0))
    return box


def state_label(state):
    """Symbol stavu; význam nesie aj text v tooltipe a v prístupnosti, nielen farba."""
    glyph = Gtk.Label(label=model.state_glyph(state))
    glyph.add_css_class("status-glyph")
    glyph.add_css_class(state)
    glyph.set_tooltip_text(model.state_text(state))
    glyph.update_property([Gtk.AccessibleProperty.LABEL], [model.state_text(state)])
    return glyph


def link_row(icon, title, subtitle, on_click, trailing=None):
    """Riadok, ktorý niekam vedie (stránka, oblasť, správca)."""
    button = Gtk.Button()
    button.add_css_class("flat")
    button.add_css_class("settings-row")
    button.add_css_class("link-row")
    row = Gtk.Box(spacing=12)
    image = Gtk.Image.new_from_icon_name(icon)
    image.set_pixel_size(20)
    row.append(image)
    text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
    text.append(label(title, "row-title"))
    if subtitle:
        text.append(label(subtitle, "row-note"))
    row.append(text)
    if trailing is not None:
        row.append(trailing)
    row.append(Gtk.Image.new_from_icon_name("go-next-symbolic"))
    button.set_child(row)
    button.connect("clicked", lambda _b: on_click())
    return button


class View:
    """Stránka v okne: widget plus upratanie a skok na konkrétne nastavenie."""

    widget = None

    def cleanup(self):
        pass

    def focus_key(self, key_id):
        pass


def scrolled_page(title, lead, *children):
    """Posúvateľná stránka: názov, vysvetlenie a obsah."""
    body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    body.add_css_class("settings-page")
    body.append(label(title, "page-title"))
    if lead:
        body.append(label(lead, "page-lead"))
    for child in children:
        body.append(child)
    scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_child(body)
    return scroll, body


def short_path(path):
    home = os.path.expanduser("~")
    return "~" + path[len(home):] if path.startswith(home + os.sep) else path


# ---------------------------------------------------------------- domov a oblasti
class HomeView(View):
    """Stavový prehľad (kap. 5): nie ďalšia kategória, ale rozcestník s aktuálnym stavom."""

    def __init__(self, window):
        registry = window.registry
        rows = []
        for gid, title in registry.groups.items():
            status = window.statuses[gid]
            rows.append(link_row(AREA_ICONS[gid], title, status.summary,
                                 lambda g=gid: window.show_area(g), state_label(status.state)))
        recent = [registry.page(p) for p in window.recent if any(x.id == p for x in registry.pages)]
        if recent:
            recent_rows = [link_row(p.icon or "emblem-system-symbolic", p.title, registry.groups[p.group],
                                    lambda pg=p: window.show_page(pg)) for p in recent]
            recent_block = settings_group(recent_rows)
        else:
            recent_block = label("Zatiaľ nič. Tu sa ukážu stránky, ktoré si otvoril naposledy.", "row-note")
        self.widget, _body = scrolled_page(
            "Nastavenia",
            "Stav systému a cesta ku každému nastaveniu. Hľadať môžeš hore (Ctrl+F), aj podľa hodnoty.",
            group_title("Stav systému"), settings_group(rows),
            group_title("Nedávno použité"), recent_block)


class AreaView(View):
    """Prehľad oblasti: jej stránky so stavom."""

    def __init__(self, window, gid):
        registry = window.registry
        status = window.statuses[gid]
        rows = []
        for page in registry.area_pages(gid):
            tag = label(model.PAGE_STATUS_TEXT[page.status], "row-note", wrap=False)
            rows.append(link_row(page.icon or "emblem-system-symbolic", page.title, page.description,
                                 lambda pg=page: window.show_page(pg), tag))
        head = Gtk.Box(spacing=8)
        head.append(state_label(status.state))
        head.append(label(status.summary, "row-note"))
        self.widget, _body = scrolled_page(registry.groups[gid], registry.group_notes.get(gid, ""),
                                           head, group_title("Stránky"), settings_group(rows))


# ---------------------------------------------------------------- stránky
class SchemaView(View):
    """Stránka poskladaná zo schémy domény; kľúče rieši Store, nie tento kód."""

    def __init__(self, window, page):
        self.window = window
        self.store = window.store(page.domain)
        self.rows = {}
        blocks = []
        if self.store.problems:
            blocks.append(notice("Súbor s nastaveniami má chyby, použili sa predvolené hodnoty:\n"
                                 + "\n".join(self.store.problems), danger=True))
        for _section, title, keys in window.registry.page_sections(page):
            rows = []
            for key in keys:
                row = KeyRow(self.store, key)
                self.rows[key.id] = row
                rows.append(row)
            if title:
                blocks.append(group_title(title))
            blocks.append(settings_group(rows))
        foot = label("Hodnoty sa ukladajú do %s." % short_path(self.store.path), "row-note")
        foot.set_margin_top(16)
        blocks.append(foot)
        self.widget, _body = scrolled_page(page.title, page.description, *blocks)
        # súbor môže zmeniť aj iný nástroj (latte-appearance set ...): riadky si zobrazia nové hodnoty
        self.monitor = settings.watch([self.store.domain.file], self.on_external)

    def on_external(self):
        self.store.reload()
        for row in self.rows.values():
            row.refresh()

    def cleanup(self):
        if self.monitor is not None:
            self.monitor.cancel()
            self.monitor = None

    def focus_key(self, key_id):
        row = self.rows.get(key_id)
        if row is not None:
            GLib.idle_add(row.flash)


class PlannedView(View):
    """Stránka, ktorá ešte nie je hotová: povie to poctivo a ukáže, čo bude obsahovať."""

    def __init__(self, window, page):
        blocks = []
        if page.status == "planned":
            when = " (etapa %s)" % page.etapa if page.etapa else ""
            blocks.append(notice("Táto stránka ešte nie je hotová%s." % when))
        elif page.status == "partial":
            blocks.append(notice("Časť tejto stránky ešte nie je hotová."))
        if page.contents:
            blocks.append(group_title("Bude obsahovať"))
            blocks.append(settings_group([label("•  " + item, "settings-row") for item in page.contents]))
        if page.launch:
            blocks.append(group_title("Špecializovaný správca"))
            blocks.append(settings_group([manager_row(window, page)]))
        elif page.owner:
            note = label("Operácie vlastní: %s." % page.owner, "row-note")
            note.set_margin_top(16)
            blocks.append(note)
        self.widget, _body = scrolled_page(page.title, page.description, *blocks)


def manager_row(window, page):
    name = MANAGER_NAMES.get(page.launch, page.owner)
    return link_row("folder-open-symbolic", "Otvoriť: %s" % name, "Pokročilé operácie a prehliadanie",
                    window.launch_files)


def os_pretty_name():
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return ""


class AboutView(View):
    """O LatteOS: iba informácie, nie diagnostika (kap. 52)."""

    def __init__(self, window, page):
        session = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("XDG_SESSION_DESKTOP") or ""
        rows = [
            info_row("Systém", build.NAME),
            info_row("Zostava", "%s (%s)" % (build.label(), "vývojová" if build.is_dev() else "vydanie")),
            info_row("Základ", os_pretty_name()),
            info_row("Jadro", platform.release()),
            info_row("Zariadenie", platform.node()),
            info_row("Používateľ", window.facts["user"]),
            info_row("Relácia", session),
            info_row("GTK", "%d.%d.%d" % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())),
            info_row("Python", platform.python_version()),
            info_row("Dáta LatteOS", short_path(paths.data_dir()), mono=True),
        ]
        self.widget, _body = scrolled_page(page.title, page.description, group_title("Tento systém"), settings_group(rows))


class StorageView(View):
    """Používateľský pohľad na spotrebu miesta. Oddiely, SMART a formátovanie tu nie sú."""

    def __init__(self, window, page):
        blocks = []
        volumes = vol_mod.list_volumes()
        if vol_mod.problem:
            blocks.append(notice(vol_mod.problem, danger=True))
        rows = []
        for volume in volumes:
            rows.append(self.volume_row(volume))
        blocks.append(group_title("Zväzky"))
        blocks.append(settings_group(rows) if rows else label("Nenašiel sa žiadny zväzok.", "row-note"))
        blocks.append(group_title("Správca súborov"))
        blocks.append(settings_group([manager_row(window, page)]))
        self.widget, _body = scrolled_page(page.title, page.description, *blocks)

    @staticmethod
    def volume_row(volume):
        row = Gtk.Box(spacing=12)
        row.add_css_class("settings-row")
        image = Gtk.Image.new_from_icon_name(volume.icon_name + "-symbolic")
        image.set_pixel_size(20)
        row.append(image)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
        text.append(label("%s · %s" % (volume.name, volume.kind_text), "row-title"))
        shown = False
        if volume.mounted:
            try:
                st = os.statvfs(volume.path)
                total, free = st.f_blocks * st.f_frsize, st.f_bavail * st.f_frsize
                if total:
                    used = 1 - free / total
                    state = model.usage_state(free, total)
                    bar = Gtk.ProgressBar(fraction=used)
                    bar.add_css_class("usage")
                    if state != "ok":
                        bar.add_css_class(state)
                    text.append(bar)
                    detail = "%s voľných z %s (%d %% obsadené)" % (
                        model.format_size(free), model.format_size(total), round(used * 100))
                    line = Gtk.Box(spacing=6)
                    if state != "ok":       # stav nesie aj symbol a text, nie len farba
                        line.append(state_label(state))
                        detail += " · " + ("takmer plné" if state == "problem" else "dochádza miesto")
                    line.append(label(detail, "row-note"))
                    text.append(line)
                    shown = True
            except OSError as err:
                text.append(label("Miesto sa nepodarilo zistiť: %s" % (err.strerror or err), "row-error"))
                shown = True
        if not shown and not volume.mounted:
            text.append(label(volume.state_text, "row-note"))
        row.append(text)
        return row


# ---------------------------------------------------------------- výsledky hľadania
class ResultsView(View):
    """Výsledky hľadania: rýchla cesta cez celú štruktúru (kap. 13); Enter alebo klik otvorí nastavenie."""

    def __init__(self, window, hits, query):
        rows = []
        for hit in hits:
            icon = hit.page.icon or "emblem-system-symbolic"
            rows.append(link_row(icon, hit.title, hit.path,
                                 lambda h=hit: window.open_hit(h)))
        if rows:
            blocks = [settings_group(rows)]
        else:
            blocks = [label("Pre „%s“ sa nič nenašlo. Skús kratšie slovo alebo synonymum (napr. wifi, tmavý, tapeta)." % query,
                            "row-note")]
        self.widget, _body = scrolled_page("Výsledky hľadania", model.results_text(len(hits)) if hits else "", *blocks)


# ---------------------------------------------------------------- inšpektor vpravo
class Inspector(Gtk.Box):
    """Stav, vlastník a odkaz stránky (ako inšpektor vo ForkLifte, kap. 74)."""

    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window = window
        self.add_css_class("files-inspector")
        self.set_size_request(270, -1)
        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.body.set_margin_top(16)
        self.body.set_margin_bottom(16)
        self.body.set_margin_start(16)
        self.body.set_margin_end(16)
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(self.body)
        self.append(scroll)

    def clear(self):
        child = self.body.get_first_child()
        while child is not None:
            following = child.get_next_sibling()
            self.body.remove(child)
            child = following

    def line(self, key, value, mono=False):
        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        row.add_css_class("inspector-row")
        row.append(label(key, "detail-key dim-label"))
        row.append(label(value, "mono" if mono else "", selectable=True))
        self.body.append(row)

    def show_page(self, page):
        self.clear()
        title = label(page.title, "inspector-title")
        self.body.append(title)
        head = Gtk.Box(spacing=8)
        state = {"ready": "ok", "partial": "attention", "planned": "planned"}[page.status]
        head.append(state_label(state))
        head.append(label(model.PAGE_STATUS_TEXT[page.status], "dim-label"))
        self.body.append(head)

        heading = label("STAV", "section-title")
        self.body.append(heading)
        self.line("Oblasť", self.window.registry.groups[page.group])
        if page.owner:
            self.line("Vlastník operácií", page.owner)
        if page.status == "planned" and page.etapa:
            self.line("Etapa", page.etapa)
        self.line("Adresa", page.uri, mono=True)

        if page.domain:
            store = self.window.store(page.domain)
            heading = label("HODNOTY", "section-title")
            self.body.append(heading)
            self.line("Súbor", short_path(store.path), mono=True)
            self.line("Vrstvy", "predvolené < správca < používateľ")
            if store.domain.owner:
                self.line("Používa", store.domain.owner)
        if page.launch:
            button = Gtk.Button(label="Spravovať v: %s" % MANAGER_NAMES.get(page.launch, page.owner))
            button.add_css_class("suggested-action")
            button.set_margin_top(16)
            button.connect("clicked", lambda _b: self.window.launch_files())
            self.body.append(button)
