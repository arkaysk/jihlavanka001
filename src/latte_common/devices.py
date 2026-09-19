"""Detekcia zariadení a zdrojov dát: prvá časť manažéra zariadení LatteOS.

Zistí, čo je pripojené k počítaču a čo z toho sú zdroje dát: disky, USB disky, optická
mechanika, disketa a zdieľané priečinky (VirtualBox, SMB, NFS). Nič nepripája ani nemení.
Výsledok je zoznam Device; správca súborov ho berie cez latte_common.volumes.

Zdroje údajov: `lsblk` (blokové zariadenia), /proc/self/mountinfo (zdieľané priečinky)
a ACPI (radič disketovej mechaniky, ktorý sa bez ovládača nikde inde neukáže).
"""
import json
import os
import subprocess
from dataclasses import dataclass

from gi.repository import GLib

# Poradie v zozname zariadení
KIND_ORDER = {"system": 0, "disk": 1, "usb": 2, "optical": 3, "floppy": 4, "share": 5}
KIND_TEXT = {
    "system": "Systémový disk",
    "disk": "Interný disk",
    "usb": "USB disk",
    "optical": "Optická mechanika",
    "floppy": "Disketová mechanika",
    "share": "Zdieľaný priečinok",
}
STATE_TEXT = {
    "mounted": "",
    "unmounted": "nepripojený",
    "no-fs": "bez súborového systému",
    "no-media": "bez média",
    "locked": "šifrovaný",
    "no-driver": "nedostupná",
}
# Skrátené texty stavu (bočný panel je úzky)
STATE_SHORT = {**STATE_TEXT, "no-fs": "bez súb. systému"}
# Vysvetlenie pre používateľa, keď sa zariadenie nedá otvoriť ako zväzok
STATE_HELP = {
    "no-fs": "Zariadenie nemá súborový systém, nie sú v ňom žiadne súbory. Formátovanie pribudne neskôr.",
    "no-media": "V mechanike nie je médium.",
    "locked": "Zväzok je šifrovaný. Odomykanie zatiaľ nie je podporované.",
    "no-driver": "Firmvér hlási disketovú mechaniku, ale jadro s ňou nevie pracovať "
                 "(ovládač floppy nenašiel radič).",
}

# Súborové systémy, ktoré nie sú zväzok (výmenná oblasť, členovia LVM/RAID)
NOT_MOUNTABLE = {"swap", "LVM2_member", "linux_raid_member", "zfs_member"}
# Zdieľané priečinky: súborové systémy, ktoré sú sieťou alebo hostiteľom
SHARE_FS = {"vboxsf", "cifs", "smb3", "smbfs", "nfs", "nfs4", "9p", "virtiofs", "fuse.sshfs"}
# Pripojenia, ktoré sú vnútro systému a nie sú zdrojom dát (okrem /run/media/…)
HIDDEN_MOUNTS = ("/boot", "/proc", "/sys", "/run", "/dev")
# Blokové zariadenia, ktoré nie sú disky (pamäťové disky, slučky)
IGNORED_NAMES = ("loop", "ram", "zram", "nbd")
FLOPPY_MAJOR = "2"

LSBLK_COLUMNS = "NAME,PATH,KNAME,MAJ:MIN,TYPE,RM,RO,TRAN,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS,MODEL,VENDOR"


@dataclass
class Device:
    key: str                    # stabilná identita: UUID, inak cesta zariadenia, pri zdieľaní zdroj
    kind: str                   # system | disk | usb | optical | floppy | share
    state: str                  # mounted | unmounted | no-fs | no-media | locked | no-driver
    node: str = ""              # /dev/sdb1 (pri zdieľanom priečinku prázdne)
    mountpoint: str = None
    size: int = 0               # bajty; 0 = neznáme alebo bez média
    fstype: str = ""
    label: str = ""
    uuid: str = ""
    vendor: str = ""
    model: str = ""
    bus: str = ""               # sata, usb, ata, nvme, …
    removable: bool = False
    share_name: str = ""

    @property
    def kind_text(self):
        return KIND_TEXT[self.kind]

    @property
    def state_text(self):
        return STATE_TEXT[self.state]

    @property
    def mountable(self):
        return self.state == "unmounted"


def format_size(size):
    return GLib.format_size(size) if size else ""


# ---------------------------------------------------------------- blokové zariadenia
def _first_mountpoint(node):
    for point in node.get("mountpoints") or []:
        if point:
            return point
    return None


def _kind(node, mountpoint):
    if mountpoint == "/":
        return "system"
    if str(node.get("maj:min", "")).split(":")[0] == FLOPPY_MAJOR or str(node.get("kname", "")).startswith("fd"):
        return "floppy"
    if node.get("type") == "rom" or str(node.get("kname", "")).startswith("sr"):
        return "optical"
    if node.get("tran") == "usb":
        return "usb"
    return "disk"


def _clean(text):
    return (text or "").strip()


def _from_node(node, out, inherit):
    """Zoberie uzol lsblk a jeho potomkov. Disk s oddielmi sa neukazuje, ukážu sa jeho
    oddiely; pripojenie a druh zdedia oddiely od disku (USB, výmenné médium)."""
    node = dict(node)
    for key in ("tran", "vendor", "model"):
        if not node.get(key) and inherit.get(key):
            node[key] = inherit[key]
    node["rm"] = bool(node.get("rm")) or bool(inherit.get("rm"))
    kname = str(node.get("kname") or node.get("name") or "")
    typ = node.get("type")
    children = node.get("children") or []

    if typ == "loop" or kname.startswith(IGNORED_NAMES):
        return

    for child in children:
        _from_node(child, out, node)

    mountpoint = _first_mountpoint(node)
    fstype = node.get("fstype") or ""
    path = node.get("path") or ("/dev/" + kname)
    kind = _kind(node, mountpoint)
    removable = node["rm"] or node.get("tran") == "usb" or kind in ("optical", "floppy")
    size = int(node.get("size") or 0)

    def device(state):
        return Device(
            key=node.get("uuid") or path, kind=kind, state=state, node=path,
            mountpoint=mountpoint if state == "mounted" else None, size=size, fstype=fstype,
            label=_clean(node.get("label")), uuid=node.get("uuid") or "",
            vendor=_clean(node.get("vendor")), model=_clean(node.get("model")),
            bus=node.get("tran") or "", removable=removable)

    if mountpoint:
        if not mountpoint.startswith("/") or typ not in ("part", "disk", "lvm", "crypt", "rom"):
            return                      # aj swap ("[SWAP]"): nie je to priečinok
        if mountpoint.startswith(HIDDEN_MOUNTS) and not (removable and mountpoint.startswith("/run/media/")):
            return
        out.append(device("mounted"))
    elif fstype == "crypto_LUKS":
        out.append(device("locked"))
    elif fstype:
        if fstype not in NOT_MOUNTABLE and typ in ("part", "disk", "rom"):
            out.append(device("unmounted"))
    elif typ in ("disk", "rom") and not children:
        # zariadenie bez súborového systému (prázdny disk) alebo mechanika bez média
        media_missing = kind in ("optical", "floppy") and size == 0
        out.append(device("no-media" if media_missing else "no-fs"))


def parse_lsblk(data):
    """data: rozparsovaný JSON z `lsblk -J -b` -> zoznam Device."""
    out = []
    for node in data.get("blockdevices", []):
        _from_node(node, out, {})
    return out


def read_lsblk():
    cmd = ["lsblk", "-J", "-b", "-o", LSBLK_COLUMNS]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("lsblk zlyhal: " + (proc.stderr.strip() or "kód %d" % proc.returncode))
    return json.loads(proc.stdout)


# ---------------------------------------------------------------- zdieľané priečinky
def _unescape(field):
    """mountinfo zapisuje medzeru a pod. ako \\040."""
    out, i = [], 0
    while i < len(field):
        if field[i] == "\\" and len(field) >= i + 4 and field[i + 1:i + 4].isdigit():
            out.append(chr(int(field[i + 1:i + 4], 8)))
            i += 4
        else:
            out.append(field[i])
            i += 1
    return "".join(out)


def parse_shares(mountinfo):
    """Zdieľané priečinky z textu /proc/self/mountinfo."""
    shares, seen = [], set()
    for line in mountinfo.splitlines():
        if " - " not in line:
            continue
        left, right = line.split(" - ", 1)
        fields, tail = left.split(), right.split()
        if len(fields) < 5 or len(tail) < 2:
            continue
        mountpoint, fstype, source = _unescape(fields[4]), tail[0], _unescape(tail[1])
        if fstype not in SHARE_FS or mountpoint in seen:
            continue
        seen.add(mountpoint)
        name = os.path.basename(source.rstrip("/")) or source
        try:
            st = os.statvfs(mountpoint)
            size = st.f_blocks * st.f_frsize
        except OSError:
            size = 0
        shares.append(Device(
            key="share:%s:%s" % (fstype, source), kind="share", state="mounted", mountpoint=mountpoint,
            size=size, fstype=fstype, label=name, share_name=name, bus=fstype))
    return shares


def read_mountinfo():
    with open("/proc/self/mountinfo", encoding="utf-8", errors="replace") as f:
        return f.read()


# ---------------------------------------------------------------- disketa (ACPI)
def read_floppy_controller():
    """Firmvér hlási radič disketovej mechaniky (PNP0700) a označil ho za prítomný (_STA bit 0).
    Pri _STA = 0 je v tabuľkách len opis, zariadenie tam nie je (typicky VirtualBox bez disketovej mechaniky)."""
    base = "/sys/bus/acpi/devices"
    try:
        names = [n for n in os.listdir(base) if n.startswith("PNP0700")]
    except OSError:
        return False
    for name in names:
        try:
            with open(os.path.join(base, name, "status")) as f:
                if int(f.read().strip()) & 1:
                    return True
        except (OSError, ValueError):
            continue
    return False


# ---------------------------------------------------------------- všetko dokopy
def detect(lsblk=None, mountinfo=None, floppy_controller=None):
    """Zoznam zdrojov dát. Parametre umožňujú podvrhnúť vstupy v testoch.

    Ak lsblk zlyhá, vyhodí RuntimeError; volajúci to musí ukázať (žiadna tichá degradácia).
    """
    found = parse_lsblk(lsblk if lsblk is not None else read_lsblk())
    found += parse_shares(mountinfo if mountinfo is not None else read_mountinfo())

    if not any(d.kind == "floppy" for d in found):
        present = read_floppy_controller() if floppy_controller is None else floppy_controller
        if present:
            found.append(Device(key="floppy:controller", kind="floppy", state="no-driver", removable=True))

    found.sort(key=lambda d: (KIND_ORDER[d.kind], d.node, d.key))
    return found
