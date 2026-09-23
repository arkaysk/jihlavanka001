"""Záznam o skončení poslednej relácie (píše ho session/latteos-session).

Súbor má riadky KLÚČ=hodnota. Prihlasovacia obrazovka ho číta pred prihlásením,
takže ho vidí ktokoľvek pri obrazovke. Preto sa z neho berie len to, čo prejde
prísnou kontrolou (druh, čísla, meno signálu); log a cesty v ňom nie sú.
"""
import os
import re
from dataclasses import dataclass
from datetime import datetime

# Kam píše latteos-session pre prihlasovaciu obrazovku (tools/install-greeter.sh ho
# vytvára s sticky bitom, každý používateľ smie prepísať len svoj súbor).
SHARED_DIR = "/var/lib/latteos/last-exit"

KINDS = ("normal", "error", "crash", "killed", "missing")
QUICK_SECONDS = 5          # kratšie = relácia sa nespustila
DIAG_COMMAND = "latteos-diag"

_TOKEN = re.compile(r"^[A-Za-z0-9_-]{1,20}$")


@dataclass
class LastExit:
    time: int = 0
    kind: str = "normal"
    status: int = 0
    signal: str = ""
    uptime: int = 0
    component: str = "labwc"

    @property
    def is_problem(self):
        return self.kind != "normal"

    @property
    def quick(self):
        return self.is_problem and self.uptime < QUICK_SECONDS

    def when(self):
        if not self.time:
            return ""
        return datetime.fromtimestamp(self.time).strftime("%-d. %-m. %H:%M")


def parse(text):
    """Záznam z textu alebo None, ak nie je použiteľný."""
    fields = {}
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            fields[key.strip()] = value.strip()
    kind = fields.get("KIND")
    if kind not in KINDS:
        return None
    record = LastExit(kind=kind)
    for key, attr in (("TIME", "time"), ("STATUS", "status"), ("UPTIME", "uptime")):
        value = fields.get(key, "0")
        if value.isdigit() and len(value) < 12:
            setattr(record, attr, int(value))
    if _TOKEN.match(fields.get("SIGNAL", "")):
        record.signal = fields["SIGNAL"]
    if _TOKEN.match(fields.get("COMPONENT", "")):
        record.component = fields["COMPONENT"]
    return record


def read(username, directory=None):
    """Záznam tohto používateľa alebo None, ak nie je (alebo bola relácia v poriadku)."""
    if not _TOKEN.match(username or ""):
        return None
    path = os.path.join(directory or SHARED_DIR, username)
    try:
        # záznam je krátky; väčší súbor nie je náš
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read(2048)
    except OSError:
        return None
    record = parse(text)
    return record if record and record.is_problem else None


def describe(record):
    """(nadpis, podrobnosť) pre kartu na prihlasovacej obrazovke."""
    name = record.component
    if record.kind == "missing":
        return ("Reláciu sa nepodarilo spustiť", "%s sa nedá spustiť (kód %d)" % (name, record.status))
    if record.quick:
        title = "Relácia sa nespustila"
    elif record.kind == "crash":
        title = "Posledná relácia spadla"
    elif record.kind == "killed":
        title = "Posledná relácia bola zabitá"
    else:
        title = "Posledná relácia skončila chybou"
    if record.signal:
        detail = "%s skončil signálom %s" % (name, record.signal)
        if record.kind == "killed":
            detail += " (možno nedostatok pamäte)"
    else:
        detail = "%s skončil s kódom %d" % (name, record.status)
    if not record.quick and record.uptime:
        detail += ", bežal %s" % _duration(record.uptime)
    return title, detail


def _duration(seconds):
    if seconds < 60:
        return "%d s" % seconds
    if seconds < 3600:
        return "%d min" % (seconds // 60)
    return "%d h %d min" % (seconds // 3600, seconds % 3600 // 60)
