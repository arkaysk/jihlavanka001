"""Metabalík `latteos-base`: jeden zoznam balíkov pre všetky stroje a stav na tomto stroji.

Roadmapa, bod H.1. Zoznam je v `data/hardware/base.toml`, tento modul ho načíta, spýta sa `rpm`,
čo je nainštalované, a povie, čo chýba. **Nič neinštaluje.** Doplnenie chýbajúceho patrí do bodu H.7
(PackageKit alebo dnf s potvrdením cez polkit), aby zisťovanie zostalo len na čítanie.

Stavy balíka:
    installed   je nainštalovaný
    missing     chýba a inštaluje sa z repozitárov, ktoré sú zapnuté
    repo        chýba a jeho repozitár nie je zapnutý (RPM Fusion) — najprv súhlas používateľa
    unknown     `rpm` sa nepodarilo spýtať (dôvod je v `problems`)

Vypnutý cudzí repozitár **nie je problém**. LatteOS ho pozná a vie, čím sa zapína (`Repo.release`,
`Repo.url`), ale sám ho nezapína a na stroji, ktorý ho nepotrebuje, ho ani nespomína. Či ho tento
počítač potrebuje, povie až hwstatus.py pri konkrétnom zariadení, ktoré bez neho nefunguje.

Výsledok používa `latte-devices base`, Nastavenia (Softvér › Aktualizácie) a hwstatus.py, ktorý
z neho berie balík k zariadeniu, ktoré nefunguje.
"""
import os
import re
import subprocess
import tomllib
from dataclasses import dataclass, field

from latte_common import paths

FILE = "base.toml"
REPO_DIR = "etc/yum.repos.d"
MARK = "\x1f"                           # oddeľovač vo formáte rpm: chybové hlášky ho nikdy nemajú
STATES = ("installed", "missing", "repo", "unknown")
STATE_TITLES = {"installed": "je", "missing": "chýba", "repo": "chýba (treba repozitár)",
                "unknown": "nezistené"}


class BaseError(ValueError):
    """Zoznam balíkov sa nedá načítať."""


@dataclass
class Package:
    name: str
    group: str
    required: bool = True               # False = ponúkne sa, neinštaluje sa automaticky
    repo: str = ""                      # id repozitára, ktorý ho nesie (prázdne = Fedora)
    note: str = ""

    @property
    def arch(self):
        """'i686' pri 32-bitovom balíku pre hry, inak prázdne."""
        return self.name.split(".", 1)[1] if "." in self.name else ""


@dataclass
class Group:
    id: str
    title: str
    why: str = ""
    devices: tuple = ()                 # skupiny zariadení z hardware.GROUPS
    packages: tuple = ()

    def required(self):
        return tuple(p for p in self.packages if p.required)


@dataclass
class Repo:
    """Cudzí repozitár, ktorý LatteOS pozná, ale nezapína. `release` a `url` držia cestu, ako sa
    zapne, aby zostala otvorená aj na stroji, ktorý ho nikdy nebude potrebovať."""
    id: str
    title: str
    note: str = ""
    release: str = ""                   # balík, ktorý repozitár pridá
    url: str = ""                       # odkiaľ sa ten balík berie ($releasever doplní dnf)

    def enable_command(self):
        return "dnf install %s" % (self.url or self.release) if (self.url or self.release) else ""


@dataclass
class Plan:
    id: str = "latteos-base"
    title: str = ""
    note: str = ""
    groups: tuple = ()
    repos: dict = field(default_factory=dict)
    source: str = ""

    def packages(self):
        return [p for g in self.groups for p in g.packages]

    def for_device_group(self, gid):
        """Skupiny balíkov, ktoré sa starajú o danú skupinu zariadení ('graphics', 'audio'...)."""
        return [g for g in self.groups if gid in g.devices]


@dataclass
class Report:
    plan: Plan
    states: dict = field(default_factory=dict)      # meno balíka -> stav
    repos: frozenset = frozenset()                  # zapnuté cudzie repozitáre
    problems: list = field(default_factory=list)

    def state(self, name):
        return self.states.get(name, "unknown")

    def repo_enabled(self, repo_id):
        return repo_id in self.repos

    def repo_brings(self, repo_id):
        """Balíky, ktoré by repozitár priniesol. Vypnutý repozitár nie je problém — je to fakt;
        či ho tento stroj potrebuje, vie až hwstatus.py pri konkrétnom zariadení."""
        return tuple(sorted(p.name for p in self.plan.packages() if p.repo == repo_id))

    def by_state(self, *states, required=None):
        out = [p for p in self.plan.packages() if self.state(p.name) in states]
        return [p for p in out if required is None or p.required == required]

    @property
    def complete(self):
        """Stroj má všetko povinné (voliteľné balíky sa nepočítajú)."""
        return not self.by_state("missing", "repo", "unknown", required=True)

    def summary(self):
        missing = self.by_state("missing", "repo", required=True)
        if self.problems and not self.states:
            return "Stav balíkov sa nepodarilo zistiť."
        if not missing:
            return "Základ je úplný: všetkých %d povinných balíkov je nainštalovaných." % len(
                [p for p in self.plan.packages() if p.required])
        return "Chýba %d z %d povinných balíkov." % (
            len(missing), len([p for p in self.plan.packages() if p.required]))

    def install_commands(self):
        """Príkazy, ktoré chýbajúce doplnia, oddelene podľa toho, čo si žiadajú od používateľa:
        povinné, voliteľné a to, čo najprv potrebuje zapnúť cudzí repozitár. Nespúšťajú sa,
        ukazujú sa (zásada 6 a bod H.7: dopĺňa sa len s potvrdením)."""
        commands = []
        for required, label in ((True, "povinné"), (False, "voliteľné, ponúkne sa")):
            names = sorted(p.name for p in self.by_state("missing", required=required) if not p.repo)
            if names:
                commands.append("# %s" % label)
                commands.append("dnf install " + " ".join(names))
        for repo_id in sorted({p.repo for p in self.by_state("missing", "repo") if p.repo}):
            names = sorted(p.name for p in self.by_state("missing", "repo") if p.repo == repo_id)
            repo = self.plan.repos.get(repo_id)
            commands.append("# repozitár %s%s" % (repo.title if repo else repo_id,
                                                  " — zapnúť len s výslovným súhlasom" if repo else ""))
            if repo and not self.repo_enabled(repo_id) and repo.enable_command():
                commands.append(repo.enable_command())
            commands.append("dnf install " + " ".join(names))
        return commands


# ---------------------------------------------------------------- načítanie zoznamu
def parse(data, source=FILE):
    """Plan z rozobratého TOML. BaseError, ak chýba to, bez čoho zoznam nedáva zmysel."""
    base = data.get("base", {})
    repos = {rid: Repo(rid, info.get("title", rid), info.get("note", ""),
                       info.get("release", ""), info.get("url", ""))
             for rid, info in (data.get("repo") or {}).items()}
    groups = []
    for raw in data.get("group") or ():
        gid = raw.get("id")
        if not gid:
            raise BaseError("%s: skupina bez 'id'" % source)
        packages = [Package(name, gid) for name in raw.get("required", ())]
        packages += [Package(name, gid, required=False) for name in raw.get("optional", ())]
        for extra in raw.get("extra", ()):
            repo_id = extra.get("repo", "")
            if repo_id and repo_id not in repos:
                raise BaseError("%s: skupina %s odkazuje na neznámy repozitár %r" % (source, gid, repo_id))
            packages += [Package(name, gid, required=False, repo=repo_id, note=extra.get("note", ""))
                         for name in extra.get("packages", ())]
        if not packages:
            raise BaseError("%s: skupina %s nemá ani jeden balík" % (source, gid))
        groups.append(Group(gid, raw.get("title", gid), raw.get("why", ""),
                            tuple(raw.get("devices", ())), tuple(packages)))
    if not groups:
        raise BaseError("%s: zoznam nemá ani jednu skupinu" % source)
    return Plan(base.get("id", "latteos-base"), base.get("title", ""), base.get("note", ""),
                tuple(groups), repos, source)


def load(data_dir=None):
    path = os.path.join(data_dir or paths.data_dir(), "hardware", FILE)
    try:
        with open(path, "rb") as stream:
            data = tomllib.load(stream)
    except OSError as err:
        raise BaseError("zoznam balíkov sa nedá čítať: %s" % err) from None
    except tomllib.TOMLDecodeError as err:
        raise BaseError("%s: poškodený súbor (%s)" % (path, err)) from None
    return parse(data, path)


# ---------------------------------------------------------------- stav stroja
def rpm_query(names, run=None):
    """{meno: verzia} pre nainštalované balíky. Jedno volanie `rpm`, bez ohľadu na návratový kód:
    pri chýbajúcom balíku rpm vracia 1 a píše preloženú hlášku, ktorá náš oddeľovač nemá."""
    if not names:
        return {}
    run = run or _run_rpm
    text = run(["rpm", "-q", "--qf", "%{NAME}" + MARK + "%{VERSION}-%{RELEASE}" + MARK + "%{ARCH}\n",
                *sorted({n.split(".", 1)[0] for n in names})])
    found = {}
    for line in text.splitlines():
        parts = line.split(MARK)
        if len(parts) == 3:
            found.setdefault(parts[0], []).append((parts[1], parts[2]))
    return found


def _run_rpm(argv):
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError) as err:
        raise OSError("%s: %s" % (argv[0], err)) from None
    return done.stdout


REPO_ID = re.compile(r"^\[([^\]]+)\]")
REPO_ENABLED = re.compile(r"^\s*enabled\s*=\s*(\S+)")


def parse_repo_file(text):
    """{id repozitára: zapnutý?} z jedného .repo súboru."""
    repos, current = {}, None
    for line in text.splitlines():
        head = REPO_ID.match(line)
        if head:
            current = head.group(1)
            repos[current] = True                      # bez kľúča enabled je repozitár zapnutý
            continue
        state = REPO_ENABLED.match(line)
        if state and current:
            repos[current] = state.group(1).strip().lower() in ("1", "true", "yes")
    return repos


def enabled_repos(root="/"):
    """Id zapnutých repozitárov z /etc/yum.repos.d. Číta sa priamo, aby sa nespúšťal dnf (je pomalý
    a chcel by metadáta zo siete)."""
    directory = os.path.join(root, REPO_DIR.lstrip("/"))
    found = set()
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return found
    for name in names:
        if not name.endswith(".repo"):
            continue
        try:
            with open(os.path.join(directory, name), encoding="utf-8", errors="replace") as stream:
                text = stream.read()
        except OSError:
            continue
        found |= {rid for rid, on in parse_repo_file(text).items() if on}
    return found


def check(plan=None, root="/", run=None, data_dir=None):
    """Report: stav každého balíka zo zoznamu na tomto stroji. Len čítanie."""
    plan = plan or load(data_dir)
    report = Report(plan, repos=frozenset(enabled_repos(root)))
    names = [p.name for p in plan.packages()]
    try:
        installed = rpm_query(names, run)
    except OSError as err:
        report.problems.append("Stav balíkov sa nedá zistiť: %s" % err)
        return report
    if not installed:
        report.problems.append("`rpm` nevrátil ani jeden balík; stav je nespoľahlivý.")
    for package in plan.packages():
        base_name, arch = package.name.split(".", 1)[0], package.arch
        builds = installed.get(base_name, [])
        if builds and (not arch or any(a == arch for _, a in builds)):
            report.states[package.name] = "installed"
        elif package.repo and package.repo not in report.repos:
            report.states[package.name] = "repo"
        else:
            report.states[package.name] = "missing"
    return report
