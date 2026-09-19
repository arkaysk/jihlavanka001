"""Zväzky LatteOS: zisťovanie diskov a mapovanie na mená Device1, Device2..."""
import json
import os
import subprocess

CONFIG_DIR = os.path.expanduser("~/.config/latteos")
CONFIG_FILE = os.path.join(CONFIG_DIR, "volumes.toml")

# Čo sa zobrazí v koreni systémového zväzku namiesto /usr, /var, /etc
SYSTEM_ENTRIES = [
    ("Apps", "/var/lib/latteos/apps"),
    ("Users", "/home"),
    ("Shared", "/srv"),
]

# Súborové systémy, ktoré nemá zmysel pripájať ako zväzok
NOT_MOUNTABLE = {"swap", "crypto_LUKS", "LVM2_member", "linux_raid_member", "zfs_member"}

_known_volumes = []


class Volume:
    """path je None, kým zväzok (výmenný disk) nie je pripojený."""

    def __init__(self, name, path, uuid="", role="data", removable=False, size="", device=""):
        self.name = name
        self.path = path
        self.uuid = uuid
        self.role = role
        self.removable = removable
        self.size = size
        self.device = device

    @property
    def mounted(self):
        return self.path is not None

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


def _flatten(node, out, inherit=None):
    """Potomkovia (partície) zdedia príznak výmenného disku od rodiča."""
    inherit = inherit or {}
    for key in ("rm", "tran"):
        if not node.get(key) and inherit.get(key):
            node[key] = inherit[key]
    out.append(node)
    for child in node.get("children", []):
        _flatten(child, out, node)


def _block_devices():
    cmd = ["lsblk", "-J", "-o", "NAME,PATH,UUID,FSTYPE,SIZE,MOUNTPOINT,RM,TRAN,TYPE,LABEL"]
    raw = subprocess.run(cmd, capture_output=True, text=True).stdout
    nodes = []
    for dev in json.loads(raw).get("blockdevices", []):
        _flatten(dev, nodes)
    return nodes


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


def list_volumes():
    names = _load_names()
    fixed, removable = [], []

    for dev in _block_devices():
        mount = dev.get("mountpoint")
        removable_dev = bool(dev.get("rm")) or dev.get("tran") == "usb"
        if not mount:
            # nepripojený výmenný disk so súborovým systémom: ukáže sa a pripojí sa pri otvorení
            fstype = dev.get("fstype")
            if not (removable_dev and fstype and fstype not in NOT_MOUNTABLE and dev.get("path")):
                continue
        elif not mount.startswith("/") or dev.get("type") not in ("part", "disk", "lvm", "crypt"):
            continue                    # aj swap ("[SWAP]"): nie je to priečinok
        elif mount.startswith(("/boot", "/proc", "/sys", "/run", "/dev")) and not (
            removable_dev and mount.startswith("/run/media/")
        ):
            continue

        uuid = dev.get("uuid") or ""
        role = "system" if mount == "/" else "data"
        vol = Volume(
            name=names.get(uuid, ""),
            path=mount or None,
            uuid=uuid,
            role=role,
            removable=removable_dev,
            size=dev.get("size") or "",
            device=dev.get("path") or "",
        )
        (removable if vol.removable else fixed).append(vol)

    fixed.sort(key=lambda v: (v.role != "system", v.path))

    used = {v.name for v in fixed if v.name}
    counter = 1
    for v in fixed:
        if not v.name:
            while "Device%d" % counter in used:
                counter += 1
            v.name = "Device%d" % counter
            used.add(v.name)

    counter = len(fixed) + 1
    for v in removable:
        v.name = "Device%d" % counter
        counter += 1

    result = fixed + removable

    global _known_volumes
    _known_volumes = result

    _save_names(result)
    return result


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
