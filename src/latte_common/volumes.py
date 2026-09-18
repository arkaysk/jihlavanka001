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

_known_volumes = []


class Volume:
    def __init__(self, name, path, uuid="", role="data", removable=False, size=""):
        self.name = name
        self.path = path
        self.uuid = uuid
        self.role = role
        self.removable = removable
        self.size = size

    def entries(self):
        """Obsah koreňa zväzku. Systémový zväzok ukazuje len vybrané miesta."""
        if self.role == "system":
            return [(n, p) for n, p in SYSTEM_ENTRIES if os.path.isdir(p)]
        return None


def _flatten(node, out):
    out.append(node)
    for child in node.get("children", []):
        _flatten(child, out)


def _block_devices():
    cmd = ["lsblk", "-J", "-o", "NAME,UUID,FSTYPE,SIZE,MOUNTPOINT,RM,TYPE,LABEL"]
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
        if not mount or dev.get("type") not in ("part", "disk", "lvm", "crypt"):
            continue
        if mount.startswith(("/boot", "/proc", "/sys", "/run", "/dev")):
            continue

        uuid = dev.get("uuid") or ""
        role = "system" if mount == "/" else "data"
        vol = Volume(
            name=names.get(uuid, ""),
            path=mount,
            uuid=uuid,
            role=role,
            removable=bool(dev.get("rm")),
            size=dev.get("size") or "",
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