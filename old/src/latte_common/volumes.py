"""Zväzky LatteOS: zdroje dát z detekcie zariadení (latte_common.devices) a ich mená Device1, Device2..."""
import os
import sys

from latte_common import devices

CONFIG_DIR = os.path.expanduser("~/.config/latteos")
CONFIG_FILE = os.path.join(CONFIG_DIR, "volumes.toml")

# Čo sa zobrazí v koreni systémového zväzku namiesto /usr, /var, /etc
SYSTEM_ENTRIES = [
    ("Apps", "/var/lib/latteos/apps"),
    ("Users", "/home"),
    ("Shared", "/srv"),
]

_known_volumes = []
problem = ""                    # prečo sa zoznam zariadení nepodarilo zistiť ("" = všetko v poriadku)


class Volume:
    """Zdroj dát. path je None, kým zväzok nie je pripojený; kind a state pochádzajú z detekcie
    (devices.Device): system | disk | usb | optical | floppy | share."""

    def __init__(self, name, path, uuid="", role="data", removable=False, size="", device="",
                 kind="disk", state=None, label="", model="", fstype=""):
        self.name = name
        self.path = path
        self.uuid = uuid
        self.role = role
        self.removable = removable
        self.size = size
        self.device = device
        self.kind = kind
        self.state = state or ("mounted" if path else "unmounted")
        self.label = label
        self.model = model
        self.fstype = fstype

    @property
    def mounted(self):
        return self.path is not None

    @property
    def mountable(self):
        """Nepripojený zväzok so súborovým systémom, ktorý sa dá pripojiť."""
        return self.state == "unmounted"

    @property
    def kind_text(self):
        return devices.KIND_TEXT[self.kind]

    @property
    def state_text(self):
        return devices.STATE_TEXT[self.state]

    @property
    def state_short(self):
        return devices.STATE_SHORT[self.state]

    @property
    def help_text(self):
        """Prečo sa zväzok nedá otvoriť (prázdne, ak sa dá)."""
        return devices.STATE_HELP.get(self.state, "")

    @property
    def icon_name(self):
        return {"system": "drive-harddisk", "disk": "drive-harddisk", "usb": "drive-removable-media",
                "optical": "media-optical", "floppy": "media-floppy", "share": "folder-remote"}[self.kind]

    @property
    def key(self):
        return self.uuid or self.device or self.path

    def __eq__(self, other):
        return isinstance(other, Volume) and self.key == other.key

    def __hash__(self):
        return hash(self.key)

    def entries(self):
        """Obsah koreňa zväzku. Systémový zväzok ukazuje len vybrané miesta."""
        if self.role == "system":
            return [(n, p) for n, p in SYSTEM_ENTRIES if os.path.isdir(p)]
        return None


def _load_names():
    if not os.path.exists(CONFIG_FILE):
        return {}
    names = {}
    uuid = None
    for line in open(CONFIG_FILE, encoding="utf-8"):
        line = line.strip()
        if line.startswith("id"):
            uuid = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("name") and uuid:
            names[uuid] = line.split("=", 1)[1].strip().strip('"')
            uuid = None
    return names


def _save_names(volumes):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write("# Mapovanie zväzkov LatteOS\n")
        for v in volumes:
            if not v.uuid or v.removable:
                continue
            f.write("\n[[volume]]\n")
            f.write('id     = "%s"\n' % v.uuid)
            f.write('name   = "%s"\n' % v.name)
            f.write('role   = "%s"\n' % v.role)


def _volume(d):
    persistent = d.kind == "share" or (bool(d.uuid) and not d.removable)
    return Volume(
        name=d.share_name if d.kind == "share" else "",
        path=d.mountpoint, uuid=d.key if d.kind == "share" else d.uuid,
        role="system" if d.kind == "system" else "data", removable=d.removable,
        size=devices.format_size(d.size), device=d.node, kind=d.kind, state=d.state,
        label=d.label, model=d.model, fstype=d.fstype), persistent


def list_volumes():
    """Zdroje dát v poradí: systémový disk, ďalšie disky, USB, optické, disketa, zdieľané priečinky.

    Ak sa zariadenia nepodarilo zistiť, vráti posledný známy zoznam a dôvod je v `problem`."""
    global _known_volumes, problem
    try:
        found = devices.detect()
    except (RuntimeError, ValueError, OSError) as err:
        problem = "zoznam zariadení sa nepodarilo zistiť: %s" % err
        print("latte-devices:", problem, file=sys.stderr)
        return list(_known_volumes)
    problem = ""

    names = _load_names()
    volumes, fixed = [], []
    for d in found:
        vol, persistent = _volume(d)
        if persistent and vol.uuid in names:
            vol.name = names[vol.uuid]
        volumes.append(vol)
        if persistent and d.kind != "share":
            fixed.append(vol)

    # Device1..N: pevné zväzky si číslo pamätajú (volumes.toml), ostatné sa číslujú za nimi
    used = {v.name for v in volumes if v.name}
    counter = 1
    for v in fixed:
        if not v.name:
            while "Device%d" % counter in used:
                counter += 1
            v.name = "Device%d" % counter
            used.add(v.name)
    counter = len(fixed) + 1
    for v in volumes:
        if not v.name:
            while "Device%d" % counter in used:
                counter += 1
            v.name = "Device%d" % counter
            used.add(v.name)

    _known_volumes = volumes
    _save_names(volumes)
    return volumes


def rename(volume, new_name):
    """Zmení zobrazované meno zväzku. Interná identita (UUID) zostáva."""
    new_name = new_name.strip()
    if not new_name:
        return False
    volume.name = new_name
    _save_names(_known_volumes)
    return True


def locate(volumes, path):
    """Zväzok a koreň zobrazenia pre cestu, alebo None, ak cesta nepatrí žiadnemu zväzku
    (alebo leží mimo miest, ktoré systémový zväzok ukazuje). Koreň určuje, kam až
    sa dá ísť hore tlačidlom „..“."""
    def inside(base):
        return path == base or path.startswith(base.rstrip("/") + "/")

    best = None
    for v in volumes:
        if v.path and inside(v.path) and (best is None or len(v.path) > len(best.path)):
            best = v
    if best is None:
        return None
    entries = best.entries()
    if entries is None:
        return best, best.path
    for _label, entry in entries:
        if inside(entry):
            return best, entry
    return None
