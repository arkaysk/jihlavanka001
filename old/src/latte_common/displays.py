"""Monitory pre Nastavenia: identita, ponuka rozlíšení a uloženie voľby (displays.toml).

Čo monitor vie a čo má práve nastavené, hovorí kompozitor (outputs.py). Tu sa z toho skladá to, čo
potrebujú Nastavenia (zoznam rozlíšení, frekvencií, odporúčaná hodnota) a čo si LatteOS pamätá medzi
reláciami: kompozitor labwc si nastavenie výstupov sám nepamätá, preto ho pri prihlásení použije
`latte-devices display apply`.

Uložené je po monitore, nie po konektore: monitor sa pozná podľa výrobcu, modelu a sériového čísla,
takže voľba ostane, aj keď ho zapojíš do iného portu. Súbor: ~/.config/latteos/displays.toml.
"""
import math
import os
import re
import tomllib

from latte_common import outputs, settings

FILE = "displays.toml"
SCALES = (1.0, 1.25, 1.5, 1.75, 2.0)
TRANSFORM_LABELS = {
    "normal": "Na šírku",
    "90": "Na výšku, otočené o 90°",
    "180": "Na šírku, otočené o 180°",
    "270": "Na výšku, otočené o 270°",
}
TRANSFORMS = tuple(TRANSFORM_LABELS)     # ostatné (zrkadlené) režimy Nastavenia zatiaľ neponúkajú
MIN_WIDTH, MIN_HEIGHT = 1024, 600        # menšie rozlíšenie (640 × 480, 800 × 600) sa neponúka ani nevolí samo
SAFE_PIXELS = 1920 * 1080                # strop pre automatickú voľbu, keď monitor nehlási použiteľný preferovaný režim
RATE_TOLERANCE = 50                     # mHz: 59940 a 60000 sú pre uloženie rôzne režimy, 59940 a 59950 nie


# ---------------------------------------------------------------- identita a popis
def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def identify(heads):
    """{id: Head}; id je výrobca-model-sériové číslo, inak názov konektora; pri zhode aj konektor."""
    ids = {}
    for head in heads:
        base = slug(" ".join(x for x in (head.make, head.model, head.serial) if x)) or slug(head.name) or "monitor"
        ids.setdefault(base, []).append(head)
    out = {}
    for base, group in ids.items():
        for head in group:
            out[base if len(group) == 1 else "%s-%s" % (base, slug(head.name))] = head
    return out


def title(head):
    """Ľudský názov: „LG 27GL850“, inak popis z kompozitora, inak konektor."""
    name = " ".join(x for x in (head.make, head.model) if x)
    return name or head.description or head.name


def diagonal_inches(head):
    if head.width_mm <= 0 or head.height_mm <= 0:
        return None
    return math.hypot(head.width_mm, head.height_mm) / 25.4


def dpi(head):
    """Hustota bodov podľa aktuálneho režimu a fyzickej veľkosti; None, ak monitor veľkosť nehlási."""
    mode = head.current
    if mode is None or head.width_mm <= 0:
        return None
    return mode.width / (head.width_mm / 25.4)


# ---------------------------------------------------------------- ponuka režimov
def usable(width, height):
    return width >= MIN_WIDTH and height >= MIN_HEIGHT


def resolutions(head):
    """[(šírka, výška)] od najväčšieho. Rozlíšenia pod MIN_WIDTH × MIN_HEIGHT sa neponúkajú (okno
    Nastavení ani lišta sa naň nezmestia); ak monitor nemá žiadne väčšie, ponúknu sa všetky."""
    found = {(m.width, m.height) for m in head.modes.values() if m.width and m.height}
    good = {r for r in found if usable(*r)}
    return sorted(good or found, key=lambda r: (r[0] * r[1], r[0]), reverse=True)


def safe_modes(head):
    """[(šírka, výška, refresh)] od najvhodnejšieho pre prihlasovaciu obrazovku a prvé spustenie.

    Najprv preferovaný režim monitora, ak je použiteľný. Virtuálne grafiky bez EDID (VirtualBox, QEMU)
    ako preferovaný hlásia záložných 640 × 480, ten sa preskočí. Potom najväčšie rozlíšenia do SAFE_PIXELS:
    vyššie (4K na pixman vykresľovaní) prihlásenie zbytočne spomaľuje."""
    result = []
    for mode in head.modes.values():
        if mode.preferred and usable(mode.width, mode.height):
            result.append((mode.width, mode.height, mode.refresh))
    for width, height in resolutions(head):
        if usable(width, height) and width * height <= SAFE_PIXELS:
            candidate = (width, height, recommended_rate(head, width, height))
            if candidate not in result:
                result.append(candidate)
    return result


def recommended_resolution(head):
    """Bezpečné rozlíšenie (safe_modes: preferovaný režim monitora, ak je použiteľný), inak najväčšie."""
    safe = safe_modes(head)
    if safe:
        return safe[0][:2]
    found = resolutions(head)
    return found[0] if found else None


def rates(head, width, height):
    """Frekvencie (mHz) pre rozlíšenie od najvyššej. Neznáma frekvencia (0) sa neponúka, ak je aj iná."""
    found = sorted({m.refresh for m in head.modes.values() if (m.width, m.height) == (width, height)}, reverse=True)
    known = [r for r in found if r > 0]
    return known or found


def recommended_rate(head, width, height):
    for mode in head.modes.values():
        if mode.preferred and (mode.width, mode.height) == (width, height):
            return mode.refresh
    available = rates(head, width, height)
    return available[0] if available else 0


def pick_rate(head, width, height, wanted=None):
    """Frekvencia pre nové rozlíšenie: rovnaká ako doteraz, ak ju má, inak odporúčaná."""
    available = rates(head, width, height)
    if wanted is not None and available:
        nearest = min(available, key=lambda rate: abs(rate - wanted))
        if abs(nearest - wanted) <= RATE_TOLERANCE:
            return nearest
    return recommended_rate(head, width, height)


def recommended_scale(head):
    """Mierka podľa hustoty bodov: bežný monitor 1×, veľmi ostrý 1,5× až 2×; bez rozmerov 1×."""
    density = dpi(head)
    if density is None:
        return 1.0
    if density >= 200:
        return 2.0
    if density >= 150:
        return 1.5
    return 1.0


def format_resolution(width, height):
    return "%d × %d" % (width, height)


def format_rate(mhz):
    """59940 -> „59,94 Hz“, 60000 -> „60 Hz“, 0 -> „neznáma“."""
    if mhz <= 0:
        return "neznáma"
    hz = mhz / 1000.0
    text = ("%d" % round(hz)) if abs(hz - round(hz)) < 0.005 else ("%.2f" % hz).rstrip("0")
    return text.replace(".", ",") + " Hz"


def format_scale(scale):
    return "%d %%" % round(scale * 100)


def summary(head):
    """Jedna veta o monitore: „2560 × 1440 · 144 Hz · 100 %“."""
    mode = head.current
    if not head.enabled:
        return "vypnutý"
    if mode is None:
        return "režim neznámy"
    parts = [format_resolution(mode.width, mode.height)]
    if mode.refresh:
        parts.append(format_rate(mode.refresh))
    parts.append(format_scale(head.scale))
    return " · ".join(parts)


def change_for(head, width, height, refresh, scale, transform):
    """Zmena pre outputs.Client.apply: len to, čo sa naozaj líši od stavu monitora."""
    change = {}
    mode = head.current
    if mode is None or (mode.width, mode.height, mode.refresh) != (width, height, refresh):
        change["mode"] = (width, height, refresh)
    if abs(head.scale - scale) > 1e-3:
        change["scale"] = scale
    if outputs.TRANSFORMS.get(head.transform) != transform:
        change["transform"] = transform
    return change


def current_state(head):
    """(šírka, výška, refresh, mierka, otočenie) tak, ako je monitor práve nastavený."""
    mode = head.current
    return (mode.width if mode else 0, mode.height if mode else 0, mode.refresh if mode else 0,
            head.scale, outputs.TRANSFORMS.get(head.transform, "normal"))


# ---------------------------------------------------------------- uloženie
def config_path():
    return os.path.join(settings.config_dir(), FILE)


def load_saved(path=None):
    """({id monitora: {width, height, refresh, scale, transform}}, [problémy]). Zlý súbor nikdy nezhodí reláciu."""
    path = path or config_path()
    problems = []
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        return {}, problems
    except (OSError, tomllib.TOMLDecodeError) as err:
        return {}, ["%s sa nedá prečítať: %s" % (path, err)]
    saved = {}
    for ident, entry in (data.get("monitor") or {}).items():
        try:
            item = {
                "width": _int(entry, "width", 1), "height": _int(entry, "height", 1),
                "refresh": _int(entry, "refresh", 0),
                "scale": _scale(entry.get("scale", 1.0)),
                "transform": _transform(entry.get("transform", "normal")),
            }
        except ValueError as err:
            problems.append("%s: monitor %s: %s (použije sa to, čo je nastavené)" % (path, ident, err))
            continue
        saved[ident] = item
    return saved, problems


def _int(entry, key, minimum):
    value = entry.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError("%s: očakáva sa celé číslo od %d" % (key, minimum))
    return value


def _scale(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.5 <= value <= 4:
        raise ValueError("scale: očakáva sa číslo od 0,5 do 4")
    return float(value)


def _transform(value):
    if value not in TRANSFORMS:
        raise ValueError("transform: povolené %s" % ", ".join(TRANSFORMS))
    return value


def save_monitor(ident, width, height, refresh, scale, transform, path=None):
    """Zapíše voľbu jedného monitora (atomicky); ostatné monitory a neznáme kľúče ostanú."""
    path = path or config_path()
    _scale(scale)
    _transform(transform)
    saved, _problems = load_saved(path)
    saved[ident] = {"width": int(width), "height": int(height), "refresh": int(refresh),
                    "scale": float(scale), "transform": transform}
    _write(saved, path)


def forget_monitor(ident, path=None):
    path = path or config_path()
    saved, _problems = load_saved(path)
    if saved.pop(ident, None) is not None:
        _write(saved, path)


def _write(saved, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = "# Monitory (LatteOS). Zapisujú Nastavenia systému; pri prihlásení ich použije latte-devices display apply."
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(settings.dumps({"monitor": saved}, header))
    os.replace(tmp, path)


# ---------------------------------------------------------------- použitie uloženého
def plan_saved(heads, saved):
    """(zmeny pre apply, [poznámky]) pre monitory, ktoré majú uloženú voľbu a líšia sa od stavu."""
    changes, notes = {}, []
    by_id = identify(heads)
    for ident, want in saved.items():
        head = by_id.get(ident)
        if head is None or not head.enabled:
            continue
        if not has_mode(head, want) and head.modes:
            notes.append("%s: uložený režim %s už monitor nemá, ostáva súčasný"
                         % (title(head), format_resolution(want["width"], want["height"])))
            change = change_for(head, *current_state(head)[:3], want["scale"], want["transform"])
        else:
            change = change_for(head, want["width"], want["height"], want["refresh"], want["scale"], want["transform"])
        if change:
            changes[head.name] = change
    return changes, notes


def has_mode(head, want):
    return any((m.width, m.height, m.refresh) == (want["width"], want["height"], want["refresh"])
               for m in head.modes.values())


def safe_change(client, head):
    """Zmena režimu na najvhodnejšie rozlíšenie zo safe_modes, ktoré kompozitor prijme (skúša ich bez
    použitia). {} = netreba (už také je) alebo sa nič nepodarilo a monitor ostane, ako je."""
    current = head.current
    for mode in safe_modes(head):
        if current is not None and (current.width, current.height, current.refresh) == mode:
            return {}
        if client.apply({head.name: {"mode": mode}}, test_only=True) is None:
            return {"mode": mode}
    return {}


def apply_safe():
    """Prihlasovacia obrazovka: každý zapnutý monitor dostane najvyššie bezpečné rozlíšenie. Vráti [správy]."""
    with outputs.Client() as client:
        changes = {}
        for head in client.monitors():
            change = safe_change(client, head) if head.enabled else {}
            if change:
                changes[head.name] = change
        error = client.apply(changes) if changes else None
    return ["rozlíšenie prihlasovacej obrazovky sa nepodarilo nastaviť: %s" % error] if error else []


def apply_saved(path=None):
    """Použije uložené voľby na zapojené monitory; monitor bez uloženej (alebo použiteľnej) voľby dostane
    bezpečné rozlíšenie ako prihlasovacia obrazovka. Vráti [správy] (prázdne = nič sa nemenilo alebo hotovo)."""
    saved, problems = load_saved(path)
    messages = list(problems)
    with outputs.Client() as client:
        heads = client.monitors()
        changes, notes = plan_saved(heads, saved)
        messages += notes
        for ident, head in identify(heads).items():
            want = saved.get(ident)
            if not head.enabled or (want is not None and has_mode(head, want)):
                continue
            mode = safe_change(client, head)
            if mode:
                changes.setdefault(head.name, {}).update(mode)
        if changes:
            error = client.apply(changes)
            if error:
                messages.append("uložené nastavenie monitorov sa nepodarilo použiť: %s" % error)
    return messages
