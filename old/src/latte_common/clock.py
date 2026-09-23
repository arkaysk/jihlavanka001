"""Časové pásma a čas pre manažér času v lište (bod 2.6).

Zoznam pásiem je v ~/.config/latteos/clock.toml (zones = "Europe/London,Asia/Tokyo").
"""
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from latte_common import prefs

DEFAULT_ZONES = ["Europe/London", "America/New_York", "Asia/Tokyo"]
_DAY_WORDS = {-1: "včera", 0: "dnes", 1: "zajtra"}


def valid_zone(name):
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        return False
    return "/" in name or name in ("UTC", "GMT")


def load_zones():
    raw = prefs.load("clock").get("zones")
    if raw is None:
        return list(DEFAULT_ZONES)
    zones = []
    for name in (part.strip() for part in raw.split(",")):
        if not name or name in zones:
            continue
        if valid_zone(name):
            zones.append(name)
        else:
            print("latte-clock: pásmo „%s“ neexistuje, preskočené" % name, file=sys.stderr)
    return zones


def save_zones(zones):
    prefs.update("clock", zones=",".join(zones))


def add_zone(name):
    """Pridá pásmo; vráti chybu ako text, alebo None. Názov nezávisí od veľkosti písmen."""
    name = name.strip().replace(" ", "_")
    if not name:
        return "Napíš názov pásma, napr. Europe/Paris."
    match = next((z for z in _known() if z.lower() == name.lower()), None)
    if match is None:
        return "Pásmo „%s“ neexistuje. Tvar je Kontinent/Mesto, napr. Europe/Paris." % name
    zones = load_zones()
    if match in zones:
        return "Pásmo %s už v zozname je." % match
    save_zones(zones + [match])
    return None


def remove_zone(name):
    save_zones([z for z in load_zones() if z != name])


def _known():
    import zoneinfo
    return zoneinfo.available_timezones()


def city(name):
    return name.rsplit("/", 1)[-1].replace("_", " ")


def local_zone_name():
    """Názov miestneho pásma z /etc/localtime, alebo "" (vtedy sa ukáže len „Miestny čas“)."""
    try:
        target = os.path.realpath("/etc/localtime")
    except OSError:
        return ""
    marker = "/zoneinfo/"
    return target.split(marker, 1)[1] if marker in target else ""


def offset_text(delta_minutes):
    sign = "+" if delta_minutes >= 0 else "-"
    hours, minutes = divmod(abs(int(delta_minutes)), 60)
    return "%s%d h" % (sign, hours) if not minutes else "%s%d:%02d h" % (sign, hours, minutes)


def zone_row(now, name):
    """Čas v pásme `name` voči miestnemu času. `now` je aware datetime (ľubovoľné pásmo).
    Vráti (mesto, "HH:MM", "dnes|zajtra|včera", "+5 h")."""
    local = now.astimezone()
    there = now.astimezone(ZoneInfo(name))
    days = (there.date() - local.date()).days
    diff = (there.utcoffset() - local.utcoffset()).total_seconds() / 60
    return city(name), there.strftime("%H:%M"), _DAY_WORDS.get(days, there.strftime("%-d. %-m.")), \
        ("rovnaký čas" if diff == 0 else offset_text(diff))


def ago(now_ts, then_ts):
    """„pred 5 min“ pre zoznam oznámení."""
    seconds = max(0, int(now_ts - then_ts))
    if seconds < 60:
        return "teraz"
    if seconds < 3600:
        return "pred %d min" % (seconds // 60)
    if seconds < 86400:
        return "pred %d h" % (seconds // 3600)
    return "pred %d d" % (seconds // 86400)


def utc_now():
    return datetime.now(timezone.utc)
