"""Systémové nastavenia LatteOS: schéma, vrstvy hodnôt a ukladanie (pozri docs/nastavenia.md).

Jedna doména = jeden súbor v ~/.config/latteos/ (appearance.toml, clock.toml, ...) a jedna
schéma v data/settings/<doména>.schema.toml. Schéma hovorí, aké kľúče doména má, akého sú
typu, aké sú predvolené hodnoty a ako sa majú volať v Nastaveniach. Okno Nastavení sa z nej
skladá a odtiaľ sa hodnoty aj overujú, takže žiadny komponent si nepíše vlastný parser.

Hodnoty majú vrstvy: predvolené (schéma) < správca (/etc/latteos/<súbor>) < používateľ.
Nepoznané kľúče v súbore sa pri zápise zachovajú (novšia verzia môže mať viac kľúčov).
"""
import json
import os
import re
import sys
import tomllib
from dataclasses import dataclass, field

from latte_common import paths

TYPES = ("bool", "int", "float", "string", "enum", "color", "path")
APPLY = ("live", "session", "restart")          # kedy sa zmena prejaví
SCOPES = ("user", "system")
URI_SCHEME = "settings"
STATUSES = ("ready", "partial", "planned")
ADMIN_DIR = "/etc/latteos"
COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class SettingsError(ValueError):
    """Neplatná schéma alebo neplatná hodnota."""


def config_dir():
    """~/.config/latteos (alebo $XDG_CONFIG_HOME/latteos); číta sa pri každom volaní."""
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "latteos")


def schema_dir():
    return os.path.join(paths.data_dir(), "settings")


# ---------------------------------------------------------------- schéma
@dataclass
class Key:
    id: str                     # "color.scheme" (oddiel.kľúč) alebo "zones" (kľúč v koreni súboru)
    domain: str
    type: str
    default: object
    label: str = ""
    description: str = ""
    choices: tuple = ()
    choice_labels: tuple = ()   # texty volieb pre Nastavenia (rovnaký počet ako choices); prázdne = ukáže sa samotná voľba
    minimum: float = None
    maximum: float = None
    step: float = None
    unit: str = ""
    apply: str = "live"
    allow_empty: bool = False   # "" znamená „nenastavené“ (napr. vlastná farba akcentu)
    hidden: bool = False        # nie je v Nastaveniach (interné)

    @property
    def section(self):
        return self.id.split(".", 1)[0] if "." in self.id else ""

    @property
    def name(self):
        return self.id.split(".", 1)[1] if "." in self.id else self.id

    def choice_label(self, value):
        """Text voľby pre človeka („dark“ -> „Tmavý“)."""
        if value in self.choices and self.choice_labels:
            return self.choice_labels[self.choices.index(value)]
        return str(value)

    def validate(self, value):
        """Vráti hodnotu v kanonickom tvare alebo vyhodí SettingsError."""
        def bad(why):
            raise SettingsError("%s.%s: %s (dostal som %r)" % (self.domain, self.id, why, value))

        t = self.type
        if t == "bool":
            if not isinstance(value, bool):
                bad("očakáva sa áno/nie")
            return value
        if t in ("int", "float"):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                bad("očakáva sa číslo")
            if t == "int":
                if isinstance(value, float) and not value.is_integer():
                    bad("očakáva sa celé číslo")
                value = int(value)
            else:
                value = float(value)
            if self.minimum is not None and value < self.minimum:
                bad("najmenej %s" % self.minimum)
            if self.maximum is not None and value > self.maximum:
                bad("najviac %s" % self.maximum)
            return value
        if not isinstance(value, str) or "\0" in value:
            bad("očakáva sa text")
        if value == "":
            if not self.allow_empty:
                bad("nesmie byť prázdne")
            return value
        if t == "enum":
            if value not in self.choices:
                bad("povolené: " + ", ".join(self.choices))
            return value
        if t == "color":
            if not COLOR_RE.match(value):
                bad("očakáva sa farba #rrggbb")
            return value.upper()
        if t == "path":
            if not value.startswith("/"):
                bad("očakáva sa absolútna cesta")
            return value
        if len(value) > 4096:
            bad("príliš dlhý text")
        return value


@dataclass
class Domain:
    id: str
    title: str
    file: str
    description: str = ""
    owner: str = ""             # komponent, ktorý hodnoty používa
    scope: str = "user"
    keys: dict = field(default_factory=dict)        # id -> Key, v poradí zo schémy
    sections: dict = field(default_factory=dict)    # oddiel -> názov pre Nastavenia

    def key(self, key_id):
        try:
            return self.keys[key_id]
        except KeyError:
            raise SettingsError("doména %s nemá kľúč %s" % (self.id, key_id)) from None

    def grouped(self):
        """[(oddiel, názov, [Key, ...])] pre skladanie stránky Nastavení; skryté kľúče vynechá."""
        out = {}
        for key in self.keys.values():
            if not key.hidden:
                out.setdefault(key.section, []).append(key)
        return [(name, self.sections.get(name, name), keys) for name, keys in out.items()]


def parse_domain(data, source="<schéma>"):
    """Zo slovníka (načítaný .schema.toml) vyrobí Domain a overí, že schéma je v poriadku."""
    meta = data.get("domain")
    if not isinstance(meta, dict) or not all(isinstance(meta.get(k), str) and meta[k] for k in ("id", "title", "file")):
        raise SettingsError("%s: chýba [domain] s id, title a file" % source)
    if meta.get("scope", "user") not in SCOPES:
        raise SettingsError("%s: neznámy scope %r" % (source, meta.get("scope")))
    if not re.match(r"^[a-z][a-z0-9-]*$", meta["id"]) or "/" in meta["file"]:
        raise SettingsError("%s: neplatné id alebo file" % source)
    domain = Domain(
        id=meta["id"], title=meta["title"], file=meta["file"], description=meta.get("description", ""),
        owner=meta.get("owner", ""), scope=meta.get("scope", "user"))
    for name, section in (data.get("section") or {}).items():
        domain.sections[name] = section.get("title", name) if isinstance(section, dict) else name

    for key_id, spec in (data.get("key") or {}).items():
        where = "%s: kľúč %s" % (source, key_id)
        if not isinstance(spec, dict) or spec.get("type") not in TYPES:
            raise SettingsError("%s: neznámy type" % where)
        if not re.match(r"^[a-z][a-z0-9_-]*(\.[a-z][a-z0-9_-]*)?$", key_id):
            raise SettingsError("%s: neplatné meno (oddiel.kľúč)" % where)
        if spec.get("apply", "live") not in APPLY:
            raise SettingsError("%s: neznámy apply" % where)
        if "default" not in spec:
            raise SettingsError("%s: chýba default" % where)
        key = Key(
            id=key_id, domain=domain.id, type=spec["type"], default=spec["default"],
            label=spec.get("label", key_id), description=spec.get("description", ""),
            choices=tuple(spec.get("choices", ())), choice_labels=tuple(spec.get("labels", ())), minimum=spec.get("min"), maximum=spec.get("max"),
            step=spec.get("step"), unit=spec.get("unit", ""), apply=spec.get("apply", "live"),
            allow_empty=bool(spec.get("allow_empty", False)), hidden=bool(spec.get("hidden", False)))
        if key.type == "enum" and not key.choices:
            raise SettingsError("%s: enum bez choices" % where)
        if key.choice_labels and len(key.choice_labels) != len(key.choices):
            raise SettingsError("%s: labels a choices majú rôzny počet" % where)
        try:
            key.default = key.validate(key.default)
        except SettingsError as err:
            raise SettingsError("%s: neplatný default: %s" % (where, err)) from None
        domain.keys[key_id] = key
    return domain


@dataclass
class Page:
    id: str
    title: str
    group: str                  # oblasť: software | data | hardware | account | environment | system
    status: str = "planned"     # ready | partial | planned
    icon: str = ""
    domain: str = ""            # doména so schémou; prázdne, kým stránka nemá nastavenia v súbore
    sections: tuple = ()        # ktoré oddiely schémy stránka ukazuje (prázdne = všetky)
    description: str = ""
    keywords: tuple = ()        # synonymá pre vyhľadávanie („wifi“ nájde Sieť)
    contents: tuple = ()        # čo stránka bude obsahovať (ukáže sa, kým je plánovaná)
    owner: str = ""             # špecializovaný správca, ktorý vlastní operácie
    view: str = ""              # vlastný obsah stránky v aplikácii Nastavenia (about, storage)
    launch: str = ""            # čo otvorí „Spravovať v ...“ (files)
    etapa: str = ""             # bod z README, ktorý ju dodá
    component: str = ""

    @property
    def uri(self):
        """Odkaz na stránku, napr. settings://hardware/display."""
        return "%s://%s/%s" % (URI_SCHEME, self.group, self.id)


class Registry:
    """Všetky domény so schémami a zoznam stránok Nastavení (data/settings/)."""

    def __init__(self, directory=None):
        self.directory = directory or schema_dir()
        self.domains = {}
        self.groups = {}        # id skupiny -> názov (v poradí)
        self.group_notes = {}   # id skupiny -> krátky popis oblasti
        self.pages = []
        self._load()

    def _read(self, path):
        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError) as err:
            raise SettingsError("%s: %s" % (path, err)) from None

    def _load(self):
        try:
            names = sorted(os.listdir(self.directory))
        except OSError as err:
            raise SettingsError("schémy nastavení sa nedajú prečítať: %s" % err) from None
        for name in names:
            if name.endswith(".schema.toml"):
                path = os.path.join(self.directory, name)
                domain = parse_domain(self._read(path), path)
                if domain.id in self.domains:
                    raise SettingsError("%s: doména %s je definovaná dvakrát" % (path, domain.id))
                self.domains[domain.id] = domain
        index = os.path.join(self.directory, "index.toml")
        if not os.path.exists(index):
            return
        data = self._read(index)
        for gid, group in (data.get("group") or {}).items():
            self.groups[gid] = group.get("title", gid)
            self.group_notes[gid] = group.get("description", "")
        for spec in data.get("page", []):
            page = Page(
                id=spec["id"], title=spec["title"], group=spec.get("group", ""), status=spec.get("status", "planned"),
                icon=spec.get("icon", ""), domain=spec.get("domain", ""), sections=tuple(spec.get("sections", ())),
                description=spec.get("description", ""), keywords=tuple(spec.get("keywords", ())),
                contents=tuple(spec.get("contents", ())), owner=spec.get("owner", ""), view=spec.get("view", ""),
                launch=spec.get("launch", ""), etapa=spec.get("etapa", ""), component=spec.get("component", ""))
            if page.status not in STATUSES:
                raise SettingsError("stránka %s: neznámy status %r" % (page.id, page.status))
            if page.domain and page.domain not in self.domains:
                raise SettingsError("stránka %s: doména %s nemá schému" % (page.id, page.domain))
            if page.group not in self.groups:
                raise SettingsError("stránka %s: neznáma skupina %r" % (page.id, page.group))
            if page.sections:
                known = {k.section for k in self.domains[page.domain].keys.values()} if page.domain else set()
                for name in page.sections:
                    if name not in known:
                        raise SettingsError("stránka %s: doména %s nemá oddiel %r" % (page.id, page.domain, name))
            self.pages.append(page)

    def domain(self, domain_id):
        try:
            return self.domains[domain_id]
        except KeyError:
            raise SettingsError("neznáma doména %s" % domain_id) from None

    def page(self, page_id):
        for page in self.pages:
            if page.id == page_id:
                return page
        raise SettingsError("neznáma stránka %s" % page_id)

    def by_group(self):
        """[(id skupiny, názov, [Page, ...])] v poradí index.toml; prázdne skupiny vynechá."""
        return [(gid, title, [p for p in self.pages if p.group == gid])
                for gid, title in self.groups.items() if any(p.group == gid for p in self.pages)]

    def store(self, domain_id, **kw):
        return Store(self.domain(domain_id), **kw)

    def page_sections(self, page):
        """[(oddiel, názov, [Key, ...])] ovládacích prvkov stránky (len jej oddiely, ak ich má určené)."""
        if not page.domain:
            return []
        return [(name, title, keys) for name, title, keys in self.domains[page.domain].grouped()
                if not page.sections or name in page.sections]

    def area_pages(self, group_id):
        return [p for p in self.pages if p.group == group_id]

    @staticmethod
    def split_object(target):
        """settings://hardware/display/DP-1 -> („settings://hardware/display“, „DP-1“); bez objektu je druhé prázdne."""
        text = (target or "").strip()
        head = text[:len(URI_SCHEME) + 3] if text.startswith(URI_SCHEME + "://") else ""
        parts = [p for p in text[len(head):].split("/") if p]
        if len(parts) == 3:
            return head + "/".join(parts[:2]), parts[2]
        return text, ""

    def resolve(self, target):
        """Odkaz na miesto v Nastaveniach: („page“, Page), („area“, id oblasti) alebo None.

        Berie settings://oblasť/stránka, oblasť/stránka, samotné id stránky alebo oblasti.
        """
        text = (target or "").strip()
        prefix = URI_SCHEME + "://"
        if text.startswith(prefix):
            text = text[len(prefix):]
        parts = [p for p in text.split("/") if p]
        if not parts or len(parts) > 2:
            return None
        if len(parts) == 2:
            for page in self.pages:
                if page.group == parts[0] and page.id == parts[1]:
                    return ("page", page)
            return None
        if parts[0] in self.groups:
            return ("area", parts[0])
        for page in self.pages:
            if page.id == parts[0]:
                return ("page", page)
        return None


# ---------------------------------------------------------------- TOML zápis
def _scalar(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise SettingsError("nekonečné alebo nečíselné hodnoty sa nedajú zapísať")
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(_scalar(v) for v in value) + "]"
    raise SettingsError("nepodporovaný typ hodnoty %s" % type(value).__name__)


def dumps(data, header="", _prefix=""):
    """Malý zapisovač TOML pre vnorené slovníky skalárov a zoznamov (bez komentárov)."""
    lines = [header.rstrip("\n"), ""] if header and not _prefix else []
    scalars = {k: v for k, v in data.items() if not isinstance(v, dict)}
    tables = {k: v for k, v in data.items() if isinstance(v, dict)}
    for key, value in scalars.items():
        lines.append("%s = %s" % (key if re.match(r"^[A-Za-z0-9_-]+$", key) else json.dumps(key), _scalar(value)))
    for name, table in tables.items():
        if lines and lines[-1] != "":
            lines.append("")
        full = _prefix + name
        if any(not isinstance(v, dict) for v in table.values()) or not table:
            lines.append("[%s]" % full)
        lines.append(dumps(table, _prefix=full + ".").rstrip("\n"))
    return "\n".join(l for i, l in enumerate(lines) if l or (i and lines[i - 1] != "")).rstrip("\n") + "\n"


# ---------------------------------------------------------------- hodnoty
class Store:
    """Hodnoty jednej domény: predvolené < správca < používateľ. Zápis ide do súboru používateľa."""

    def __init__(self, domain, directory=None, admin_dir=None):
        self.domain = domain
        self.directory = directory if directory is not None else config_dir()
        self.admin_dir = admin_dir if admin_dir is not None else ADMIN_DIR
        self.problems = []
        self._raw = {}
        self._user = {}
        self._admin = {}
        self.reload()

    @property
    def path(self):
        return os.path.join(self.directory, self.domain.file)

    @property
    def admin_path(self):
        return os.path.join(self.admin_dir, self.domain.file)

    def _read_file(self, path, label):
        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except FileNotFoundError:
            return {}
        except (OSError, tomllib.TOMLDecodeError) as err:
            self.problems.append("%s sa nedá prečítať, použijú sa predvolené hodnoty: %s" % (path, err))
            print("latte-settings:", self.problems[-1], file=sys.stderr)
            return {}

    def _explicit(self, data, source):
        """Z načítaného súboru vyberie len platné kľúče zo schémy; neplatné nahlási."""
        out = {}
        for key in self.domain.keys.values():
            holder = data.get(key.section, {}) if key.section else data
            if not isinstance(holder, dict) or key.name not in holder:
                continue
            try:
                out[key.id] = key.validate(holder[key.name])
            except SettingsError as err:
                self.problems.append("%s: %s (použije sa nižšia vrstva)" % (source, err))
                print("latte-settings:", self.problems[-1], file=sys.stderr)
        return out

    def reload(self):
        self.problems = []
        self._raw = self._read_file(self.path, "user")
        self._user = self._explicit(self._raw, self.path)
        self._admin = self._explicit(self._read_file(self.admin_path, "admin"), self.admin_path)

    def get(self, key_id):
        key = self.domain.key(key_id)
        if key_id in self._user and key_id not in self._admin:
            return self._user[key_id]
        if key_id in self._admin:
            return self._admin[key_id]
        return key.default

    def source(self, key_id):
        """default | admin | user. Hodnota od správcu prekrýva používateľa (vynútené)."""
        self.domain.key(key_id)
        if key_id in self._admin:
            return "admin"
        return "user" if key_id in self._user else "default"

    def locked(self, key_id):
        return self.source(key_id) == "admin"

    def values(self):
        return {key_id: self.get(key_id) for key_id in self.domain.keys}

    def explicit(self):
        """Len to, čo používateľ nastavil (id -> hodnota)."""
        return dict(self._user)

    def set(self, key_id, value):
        self.set_many({key_id: value})

    def set_many(self, changes):
        """Zapíše viac kľúčov naraz jedným premenovaním súboru. Neplatná hodnota nezapíše nič."""
        checked = {}
        for key_id, value in changes.items():
            key = self.domain.key(key_id)
            if self.locked(key_id):
                raise SettingsError("%s.%s spravuje správca systému" % (self.domain.id, key_id))
            checked[key_id] = key.validate(value)
        raw = json.loads(json.dumps(self._raw))         # hlboká kópia; nepoznané kľúče ostanú
        for key_id, value in checked.items():
            key = self.domain.keys[key_id]
            if key.section:
                raw.setdefault(key.section, {})
                if not isinstance(raw[key.section], dict):
                    raw[key.section] = {}
                raw[key.section][key.name] = value
            else:
                raw[key.name] = value
        self._write(raw)

    def reset(self, *key_ids):
        """Vráti kľúče na predvolenú hodnotu (odstráni ich zo súboru používateľa)."""
        raw = json.loads(json.dumps(self._raw))
        for key_id in key_ids:
            key = self.domain.key(key_id)
            holder = raw.get(key.section) if key.section else raw
            if isinstance(holder, dict):
                holder.pop(key.name, None)
                if key.section and not holder:
                    raw.pop(key.section, None)
        self._write(raw)

    def _write(self, raw):
        os.makedirs(self.directory, exist_ok=True)
        header = "# %s (LatteOS). Zapisujú Nastavenia systému; ručná úprava je v poriadku." % self.domain.title
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(dumps(raw, header))
        os.replace(tmp, self.path)
        self.reload()


def watch(files, on_change, directory=None, delay_ms=150):
    """Zavolá on_change(), keď sa zmení niektorý zo súborov (mená v ~/.config/latteos/).

    Sleduje sa adresár, nie súbor: Store zapisuje cez premenovanie a súbor nemusí ešte existovať.
    Zmeny sa zlúčia (delay_ms). Vráti monitor; keď ho zahodíš, sledovanie skončí.
    """
    from gi.repository import Gio, GLib

    directory = directory if directory is not None else config_dir()
    os.makedirs(directory, exist_ok=True)
    names = set(files)
    state = {"timer": 0}

    def fire():
        state["timer"] = 0
        on_change()
        return False

    def changed(_monitor, file, other, _event):
        touched = {file.get_basename(), other.get_basename() if other else None}
        if names & touched and not state["timer"]:
            state["timer"] = GLib.timeout_add(delay_ms, fire)

    monitor = Gio.File.new_for_path(directory).monitor_directory(Gio.FileMonitorFlags.WATCH_MOVES, None)
    monitor.connect("changed", changed)
    return monitor
