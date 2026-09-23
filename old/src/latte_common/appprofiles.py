"""Profily aplikácií pre Prispôsobenie: na akej úrovni sa dá vzhľad okna vynútiť a čo sa robí, keď nie.

Úrovne (od najsilnejšej):
  enforced     vynútené: farby aj tvar preberie aplikácia cez portál alebo vlastný kód LatteOS
  aligned      zosúladené: farby preberie z konfigurácie (gtk.css, politiky), po spustení aplikácie
  recommended  odporúčané: aplikácia sa riadi len farebným režimom (tmavý/svetlý), zvyšok má vlastný
  unavailable  nedostupné: aplikácia kreslí všetko sama (hry, cudzie témy), nedá sa nič vynútiť

Náhradné riešenie (fallback), keď je úroveň slabšia ako "aligned":
  frame   kompozitor kreslí rám a titulok v téme LatteOS (aplikácia je bez vlastného pruhu)
  badge   Nastavenia a prepínač okien ukážu poctivú značku „vlastný vzhľad“
  compat  režim kompatibility: okno dostane rám a titulok, obsah ostáva nedotknutý
Farby obsahu cudzieho okna sa nikdy neinvertujú filtrom: rozbil by fotky a videá.

Profily sú súbory data/appearance-profiles/*.toml (a ~/.local/share/latteos/appearance-profiles/):
    [profile]
    id = "gnome-text-editor"
    name = "Textový editor"
    match = ["org.gnome.TextEditor"]     # app_id okna; * a ? fungujú, veľkosť písmen sa nerozlišuje
    toolkit = "gtk4"                      # kľúč z toolkits.toml, z ktorého sa berie predvolená úroveň
    level = "aligned"                     # nepovinné: prepíše úroveň nástroja
    fallback = ["badge"]                  # nepovinné: prepíše náhradné riešenie
    note = "Vysvetlenie pre používateľa."
"""
import fnmatch
import os
import tomllib
from dataclasses import dataclass, field

from latte_common import paths

LEVELS = ("enforced", "aligned", "recommended", "unavailable")
LEVEL_TITLES = {
    "enforced": "Vynútené",
    "aligned": "Zosúladené",
    "recommended": "Odporúčané",
    "unavailable": "Nedostupné",
}
FALLBACKS = ("frame", "badge", "compat")
UNKNOWN_TOOLKIT = "unknown"
BADGE_TEXT = "vlastný vzhľad"


class ProfileError(ValueError):
    """Profil je poškodený alebo neúplný."""


@dataclass
class Profile:
    id: str
    name: str
    toolkit: str
    level: str
    fallback: tuple
    note: str = ""
    match: tuple = ()

    @property
    def enforced_by_system(self):
        return self.level in ("enforced", "aligned")

    @property
    def badge(self):
        """Text značky pre okno, ktoré vzhľad LatteOS nepreberie úplne (inak None)."""
        return BADGE_TEXT if "badge" in self.fallback and not self.enforced_by_system else None


@dataclass
class Profiles:
    toolkits: dict = field(default_factory=dict)        # kľúč -> Profile (predvolené za nástroj)
    apps: list = field(default_factory=list)            # konkrétne aplikácie
    problems: list = field(default_factory=list)

    def for_app(self, app_id, toolkit=None):
        """Profil podľa app_id okna; bez zhody predvolený za nástroj, inak za neznámy nástroj."""
        wanted = (app_id or "").lower()
        for profile in self.apps:
            if any(fnmatch.fnmatchcase(wanted, pattern.lower()) for pattern in profile.match):
                return profile
        if toolkit in self.toolkits:
            return self.toolkits[toolkit]
        return self.toolkits[UNKNOWN_TOOLKIT]


def profile_dirs():
    data_home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return [os.path.join(paths.data_dir(), "appearance-profiles"),
            os.path.join(data_home, "latteos", "appearance-profiles")]


def _strings(value, what, source):
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise ProfileError("%s: %s musí byť zoznam textov" % (source, what))
    return tuple(value)


def _check_level(level, source):
    if level not in LEVELS:
        raise ProfileError("%s: neznáma úroveň %r (očakáva sa %s)" % (source, level, ", ".join(LEVELS)))
    return level


def _check_fallback(names, source):
    unknown = [n for n in names if n not in FALLBACKS]
    if unknown:
        raise ProfileError("%s: neznáme náhradné riešenie %s (očakáva sa %s)"
                           % (source, ", ".join(unknown), ", ".join(FALLBACKS)))
    return tuple(names)


def parse_toolkits(data, source="toolkits.toml"):
    table = data.get("toolkit")
    if not isinstance(table, dict) or UNKNOWN_TOOLKIT not in table:
        raise ProfileError("%s: chýba [toolkit.%s] (predvolený profil pre neznáme aplikácie)" % (source, UNKNOWN_TOOLKIT))
    out = {}
    for key, entry in table.items():
        where = "%s [toolkit.%s]" % (source, key)
        if not isinstance(entry, dict) or not entry.get("name"):
            raise ProfileError("%s: chýba name" % where)
        out[key] = Profile(
            id=key, name=entry["name"], toolkit=key,
            level=_check_level(entry.get("level"), where),
            fallback=_check_fallback(_strings(entry.get("fallback", []), "fallback", where), where),
            note=entry.get("note", ""))
    return out


def parse_app(data, toolkits, source="<profil>"):
    meta = data.get("profile")
    if not isinstance(meta, dict) or not meta.get("id") or not meta.get("name"):
        raise ProfileError("%s: chýba [profile] s id a name" % source)
    toolkit = meta.get("toolkit", UNKNOWN_TOOLKIT)
    if toolkit not in toolkits:
        raise ProfileError("%s: neznámy nástroj %r" % (source, toolkit))
    base = toolkits[toolkit]
    match = _strings(meta.get("match", []), "match", source)
    if not match:
        raise ProfileError("%s: match nesmie byť prázdny" % source)
    fallback = meta.get("fallback")
    return Profile(
        id=meta["id"], name=meta["name"], toolkit=toolkit,
        level=_check_level(meta["level"], source) if "level" in meta else base.level,
        fallback=_check_fallback(_strings(fallback, "fallback", source), source) if fallback is not None else base.fallback,
        note=meta.get("note", base.note), match=match)


def _load_toml(path):
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as err:
        raise ProfileError("%s: %s" % (path, err))


def load(directories=None):
    """Načíta profily zo všetkých adresárov (neskorší prekryje skorší). Poškodený súbor sa preskočí
    a dôvod je v Profiles.problems; bez platného toolkits.toml zlyhá celé načítanie."""
    directories = list(directories if directories is not None else profile_dirs())
    result = Profiles()
    toolkits = {}
    for directory in directories:
        path = os.path.join(directory, "toolkits.toml")
        if not os.path.exists(path):
            continue
        try:
            toolkits.update(parse_toolkits(_load_toml(path), path))
        except ProfileError as err:
            result.problems.append(str(err))
    if UNKNOWN_TOOLKIT not in toolkits:
        raise ProfileError("nenašiel sa toolkits.toml s profilom %r (hľadalo sa v %s)" % (UNKNOWN_TOOLKIT, ", ".join(directories)))
    result.toolkits = toolkits

    apps = {}
    for directory in directories:
        try:
            names = sorted(os.listdir(directory))
        except OSError:
            continue
        for name in names:
            if not name.endswith(".toml") or name == "toolkits.toml":
                continue
            path = os.path.join(directory, name)
            try:
                profile = parse_app(_load_toml(path), toolkits, path)
            except ProfileError as err:
                result.problems.append(str(err))
                continue
            apps[profile.id] = profile
    result.apps = list(apps.values())
    return result
