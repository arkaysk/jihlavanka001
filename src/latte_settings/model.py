"""Logika Nastavení systému bez GTK: vyhľadávanie, stavy oblastí, nedávne stránky.

Nastavenia integrujú stav a navigáciu, nie implementácie (main_setting_v2.md, kap. 1): tu sa
z registra (latte_common/settings.py) a zo zistených faktov skladá to, čo okno ukáže. Nič sa tu
nezapisuje; zápis ide vždy cez Store.
"""
import getpass
import os
from collections import namedtuple

from latte_common import build
from latte_common.search import fold, words

VIEWS = ("about", "storage", "display")            # vlastný obsah stránok, ktorý pozná aplikácia (Page.view)
RECENT_LIMIT = 5
MIN_FREE_ATTENTION = 0.10               # menej voľného miesta: pozornosť
MIN_FREE_PROBLEM = 0.02                 # menej voľného miesta: problém

# Stav nesmie niesť iba farba (kap. 55): symbol + text + farba.
STATES = {
    "ok": ("●", "V poriadku"),
    "attention": ("!", "Pozornosť"),
    "problem": ("×", "Problém"),
    "busy": ("↻", "Prebieha"),
    "planned": ("○", "Zatiaľ bez stavu"),
}
PAGE_STATUS_TEXT = {"ready": "Hotové", "partial": "Časť je hotová", "planned": "Plánované"}

Status = namedtuple("Status", "state summary")
Hit = namedtuple("Hit", "page key title path score")
Entry = namedtuple("Entry", "page key title path fields order")


def state_glyph(state):
    return STATES[state][0]


def state_text(state):
    return STATES[state][1]


def format_size(nbytes):
    """„85,4 GB“ (desatinná čiarka, jednotky po 1000 ako v správcovi súborov)."""
    value = float(nbytes)
    for unit in ("B", "kB", "MB", "GB", "TB"):
        if value < 1000 or unit == "TB":
            text = ("%d" % value) if unit == "B" else ("%.1f" % value).replace(".", ",")
            return "%s %s" % (text, unit)
        value /= 1000


def usage_state(free, total):
    """Stav zaplnenia disku: ok | attention | problem (jedno pravidlo pre kartu Dáta aj stránku Úložisko)."""
    if free is None or not total:
        return "attention"
    ratio = free / total
    if ratio < MIN_FREE_PROBLEM:
        return "problem"
    return "attention" if ratio < MIN_FREE_ATTENTION else "ok"


def results_text(count):
    """„1 výsledok“, „3 výsledky“, „7 výsledkov“."""
    if count == 1:
        return "1 výsledok"
    return "%d %s" % (count, "výsledky" if 2 <= count <= 4 else "výsledkov")


# ---------------------------------------------------------------- fakty a stavy oblastí
def gather_facts(registry, home=None):
    """Čo o systéme vieme zistiť lacno a bez oprávnení. Chýbajúci údaj je None, nie odhad."""
    facts = {"user": getpass.getuser(), "release": build.label(), "name": build.NAME,
             "scheme": None, "problems": 0, "free": None, "total": None}
    try:
        store = registry.store("appearance")
        facts["scheme"] = store.get("color.scheme")
        facts["problems"] = len(store.problems)
    except Exception as err:            # zlý súbor či schéma nesmú zhodiť celé okno
        facts["problems"] = 1
        facts["problem_text"] = str(err)
    try:
        st = os.statvfs(home or os.path.expanduser("~"))
        facts["free"] = st.f_bavail * st.f_frsize
        facts["total"] = st.f_blocks * st.f_frsize
    except OSError:
        pass
    return facts


def area_status(registry, group_id, facts):
    """Stav oblasti pre kartu a domovskú stránku. Bez skutočného údaja je to „len plán“, nie vymyslené OK."""
    if group_id == "account":
        return Status("ok", "Prihlásený: %s" % facts.get("user", "?"))
    if not any(p.status != "planned" for p in registry.area_pages(group_id)):
        return Status("planned", "Zatiaľ len plán")
    if group_id == "environment":
        if facts.get("problems"):
            return Status("attention", "%d problém v nastaveniach" % facts["problems"]
                          if facts["problems"] == 1 else "%d problémy v nastaveniach" % facts["problems"])
        return Status("ok", {"dark": "Tmavý motív", "light": "Svetlý motív"}.get(facts.get("scheme"), "Motív"))
    if group_id == "data":
        free, total = facts.get("free"), facts.get("total")
        if free is None or not total:
            return Status("attention", "Miesto sa nepodarilo zistiť")
        state = usage_state(free, total)
        text = "%s voľných" % format_size(free)
        return Status(state, text + (", takmer plné" if state == "problem" else ""))
    if group_id == "system":
        return Status("ok", "%s · %s" % ("LatteOS", facts.get("release", "")))
    return Status("planned", "Zatiaľ len plán")


def area_statuses(registry, facts):
    return {gid: area_status(registry, gid, facts) for gid in registry.groups}


# ---------------------------------------------------------------- hodnoty kľúčov ako text
def value_text(key, value):
    """Hodnota tak, ako ju vidí používateľ (na hľadanie podľa hodnoty: „tmavý“)."""
    if key.type == "bool":
        return "zapnuté áno" if value else "vypnuté nie"
    if key.type == "enum":
        return key.choice_label(value)
    return "" if value in (None, "") else str(value)


# ---------------------------------------------------------------- hľadanie
def build_index(registry, values=None):
    """Zoznam vyhľadateľných vecí: stránky a jednotlivé nastavenia.

    values: nepovinné volanie (page, key) -> aktuálna hodnota, aby sa dalo hľadať aj podľa nej.
    Polia majú váhy: názov najviac, potom synonymá, hodnota, popis, oblasť.
    """
    entries = []
    order = 0
    for page in registry.pages:
        area = registry.groups[page.group]
        fields = [(10, fold(page.title)), (6, fold(" ".join(page.keywords))), (3, fold(page.description)),
                  (2, fold(" ".join(page.contents))), (2, fold(area))]
        entries.append(Entry(page, None, page.title, area, fields, order))
        order += 1
        for _section, _title, keys in registry.page_sections(page):
            for key in keys:
                fields = [(10, fold(key.label)), (3, fold(key.description)), (2, fold(page.title)), (1, fold(area))]
                if values is not None:
                    current = values(page, key)
                    if current is not None:
                        fields.append((5, fold(value_text(key, current))))
                entries.append(Entry(page, key, key.label, "%s › %s" % (area, page.title), fields, order))
                order += 1
    return entries


def _word_score(word, fields):
    best = 0
    for weight, text in fields:
        if word not in text:
            continue
        starts = text.startswith(word) or (" " + word) in text
        best = max(best, weight + (3 if starts else 0))
    return best


def search(entries, query, limit=30):
    """Hit-y zoradené podľa zhody; každé slovo dotazu sa musí niekde nájsť. Diakritika nerozhoduje."""
    needles = words(query)
    if not needles:
        return []
    hits = []
    for entry in entries:
        total = 0
        for word in needles:
            got = _word_score(word, entry.fields)
            if not got:
                break
            total += got
        else:
            hits.append((-total, 0 if entry.key is None else 1, entry.order, entry))
    hits.sort(key=lambda h: h[:3])
    return [Hit(e.page, e.key, e.title, e.path, -neg) for neg, _k, _o, e in hits[:limit]]


# ---------------------------------------------------------------- nedávne stránky
def recent_parse(text):
    return [p for p in (text or "").split(",") if p]


def recent_add(recent, page_id, limit=RECENT_LIMIT):
    return ([page_id] + [p for p in recent if p != page_id])[:limit]
