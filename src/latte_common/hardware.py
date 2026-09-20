"""Správca zariadení: zistí všetok hardvér počítača, identifikuje ho a rozdelí do skupín.

Nič nemení a nepotrebuje práva správcu. Zdroje: sysfs a /proc (siete, zvuk, vstup, USB, napájanie,
DMI), `lspci` a `lsblk` (názvy a disky) a kompozitor (monitory, viď outputs.py: EDID číta on).

Každé zariadenie je v **jednej** skupine, podľa toho, čo robí, nie podľa toho, ako je zapojené:
USB klávesnica je vo Vstupných zariadeniach, USB disk v Úložisku, USB kamera v Kamerách. Skupina
USB má len to, čo inde nepatrí (tlačiareň, skener, kľúč). PCI zariadenia, ktoré už majú skupinu
(sieťová karta, zvuková karta), sa v Platforme neopakujú.

Každá skupina vie, kde sa nastavuje (`settings_uri`), takže Správca zdrojov ponúkne k zariadeniu
tlačidlo „Nastavenia“ a Nastavenia otvoria správnu stránku. Čo sa nedá zistiť, ide do `problems`
(napr. chýbajúci `lspci`), nič sa nehlási potichu ani nevymýšľa.
"""
import json
import os
import re
import subprocess
from dataclasses import dataclass, field

from latte_common import displays, outputs

# id skupiny -> (názov, stránka Nastavení). Poradie je poradie v zozname (a na záložke Zariadenia).
GROUPS = {
    "display": ("Obrazovky", "hardware/display"),
    "graphics": ("Grafické karty", "hardware/display"),
    "audio": ("Zvukové karty", "hardware/sound"),
    "network": ("Sieťové karty", "hardware/network"),
    "optical": ("Optické mechaniky", "hardware/drives"),
    "storage": ("Disky", "hardware/drives"),
    "input": ("Klávesnice, myši a iné vstupy", "hardware/bluetooth"),
    "camera": ("Kamery", "hardware/bluetooth"),
    "bluetooth": ("Bluetooth", "hardware/bluetooth"),
    "power": ("Napájanie", "hardware/power"),
    "usb": ("Iné USB", "hardware/bluetooth"),
    "computer": ("Počítač", "system/about"),
    "platform": ("Čipset a radiče", "hardware/hwdiag"),
    "connection": ("Pripojenia", "hardware/network"),
    "vpn": ("VPN", "hardware/network"),
}
# Záložky Správcu zdrojov. Sieťové karty sú na oboch: ako zariadenie aj ako súčasť siete.
TABS = (("devices", "Zariadenia"), ("networks", "Siete"))
TAB_GROUPS = {
    "devices": ("display", "graphics", "audio", "network", "optical", "storage", "input", "camera", "bluetooth",
                "power", "usb", "computer", "platform"),
    "networks": ("network", "connection", "vpn"),
}
SHOW_EMPTY = {"connection": "Žiadne uložené pripojenie.",
              "vpn": "Žiadne pripojenie VPN. Pridávanie VPN pribudne v Nastaveniach › Sieť."}
USB_COVERED = {"01", "03", "08", "09", "0e", "e0"}       # audio, HID, disk, hub, video, Bluetooth majú skupinu inde
SYSTEM_INPUTS = ("power button", "sleep button", "video bus", "lid switch", "pc speaker", "hda ", "intel hid",
                 "avs hda", "sof ")
PCI_COVERED = {"0200", "0280", "0401", "0403"}           # sieť a zvuk (majú vlastnú skupinu)


@dataclass
class Item:
    group: str
    key: str                    # stabilná identita v rámci skupiny
    name: str
    detail: str = ""            # jeden riadok podrobností: druh, veľkosť, pripojenie
    status: str = ""            # krátky stav: „pripojené“, „zapnutý“, ...
    extra: dict = field(default_factory=dict)

    @property
    def icons(self):
        """Názvy ikon od najvhodnejšej; kto kreslí, vezme prvú, ktorú téma pozná."""
        return icon_names(self)

    @property
    def settings_uri(self):
        page = GROUPS[self.group][1]
        target = self.extra.get("connector")
        return "settings://%s%s" % (page, "/" + target if target else "")


GROUP_ICONS = {
    "display": ("video-display-symbolic",),
    "graphics": ("latte-gpu-symbolic", "video-display-symbolic"),
    "audio": ("audio-card-symbolic", "audio-speakers-symbolic"),
    "network": ("network-wired-symbolic",),
    "optical": ("media-optical-symbolic", "drive-harddisk-symbolic"),
    "storage": ("drive-harddisk-symbolic",),
    "input": ("input-keyboard-symbolic",),
    "camera": ("camera-web-symbolic",),
    "bluetooth": ("bluetooth-symbolic",),
    "power": ("battery-symbolic",),
    "usb": ("drive-removable-media-symbolic",),
    "computer": ("computer-symbolic",),
    "platform": ("latte-cpu-symbolic", "emblem-system-symbolic"),
    "connection": ("network-wired-symbolic",),
    "vpn": ("network-vpn-symbolic", "security-high-symbolic"),
}
INPUT_ICONS = {"Klávesnica": "input-keyboard-symbolic", "Myš": "input-mouse-symbolic",
               "Touchpad": "input-touchpad-symbolic", "Tablet": "input-tablet-symbolic",
               "Ovládač hier": "input-gaming-symbolic", "Dotyková obrazovka": "input-tablet-symbolic"}


def icon_names(item):
    """Ikona zariadenia podľa druhu (klávesnica, Wi-Fi, SSD, batéria...), potom podľa skupiny."""
    extra = item.extra
    first = ()
    if item.group == "input":
        first = (INPUT_ICONS.get(item.detail, ""),)
    elif item.group in ("network", "connection") and extra.get("wireless"):
        first = ("network-wireless-symbolic",)
    elif item.group == "storage":
        first = {"ssd": ("drive-harddisk-solidstate-symbolic",), "usb": ("drive-removable-media-symbolic",)}.get(
            extra.get("kind"), ())
    elif item.group == "power":
        first = ("ac-adapter-symbolic",) if not extra.get("battery") else ()
    elif item.group == "computer":
        first = {"cpu": ("latte-cpu-symbolic",), "memory": ("latte-memory-symbolic",)}.get(item.key, ())
    elif item.group == "bluetooth":
        first = ("bluetooth-symbolic",)
    return tuple(n for n in first if n) + GROUP_ICONS[item.group] + ("computer-symbolic",)


@dataclass
class Inventory:
    items: list = field(default_factory=list)
    problems: list = field(default_factory=list)

    def groups(self, tab=None):
        """[(id, názov, [Item])] v stálom poradí. Bez `tab` všetky neprázdne skupiny; s `tab` skupiny záložky
        (prázdne ostanú len tie, ktoré majú vysvetlenie v SHOW_EMPTY, napr. VPN)."""
        order = TAB_GROUPS[tab] if tab else tuple(GROUPS)
        out = []
        for gid in order:
            items = [i for i in self.items if i.group == gid]
            if items or (tab and gid in SHOW_EMPTY):
                out.append((gid, GROUPS[gid][0], items))
        return out

    def group(self, gid):
        return [i for i in self.items if i.group == gid]


# ---------------------------------------------------------------- pomocné čítanie
def _path(root, *parts):
    return os.path.join(root, *[p.lstrip("/") for p in parts])


def _read(root, *parts):
    try:
        with open(_path(root, *parts), encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except OSError:
        return ""


def _listdir(root, *parts):
    try:
        return sorted(os.listdir(_path(root, *parts)))
    except OSError:
        return []


def run_command(argv):
    """Výstup príkazu ako text; OSError, ak príkaz nie je alebo zlyhal."""
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=8)
    except subprocess.SubprocessError as err:
        raise OSError("%s: %s" % (argv[0], err)) from None
    if done.returncode != 0:
        raise OSError("%s skončil s chybou %d" % (argv[0], done.returncode))
    return done.stdout


# ---------------------------------------------------------------- PCI
PCI_LINE = re.compile(r'^(\S+) "([^"]*)" "([^"]*)" "([^"]*)"')
PCI_ID = re.compile(r"^(.*) \[([0-9a-f]{4})\]$")


def parse_lspci(text):
    """{slot: {"class": "0300", "class_name", "vendor", "device"}} z `lspci -mm -nn`."""
    found = {}
    for line in text.splitlines():
        m = PCI_LINE.match(line)
        if not m:
            continue
        slot, cls, vendor, device = m.groups()
        parts = [PCI_ID.match(x) for x in (cls, vendor, device)]
        if not all(parts):
            continue
        found["0000:" + slot if slot.count(":") == 1 else slot] = {
            "class": parts[0].group(2), "class_name": parts[0].group(1),
            "vendor": parts[1].group(1), "device": parts[2].group(1)}
    return found


def _shorten_vendor(name):
    return re.sub(r"\s+(Corporation|Corp\.?|Inc\.?|Ltd\.?|GmbH|Systemberatung GmbH)$", "", name).strip()


def pci_title(info):
    return "%s %s" % (_shorten_vendor(info["vendor"]), info["device"])


# ---------------------------------------------------------------- čítače skupín
def read_computer(root):
    items = []
    vendor, product = _read(root, "sys/class/dmi/id/sys_vendor"), _read(root, "sys/class/dmi/id/product_name")
    if vendor or product:
        items.append(Item("computer", "dmi", " ".join(x for x in (vendor, product) if x),
                          "BIOS %s" % _read(root, "sys/class/dmi/id/bios_version") if _read(root, "sys/class/dmi/id/bios_version") else ""))
    cpu, cores = "", 0
    for line in _read(root, "proc/cpuinfo").splitlines():
        if line.startswith("model name") and not cpu:
            cpu = line.split(":", 1)[1].strip()
        elif line.startswith("processor"):
            cores += 1
    if cpu:
        items.append(Item("computer", "cpu", re.sub(r"\s+", " ", cpu), "%d jadier (vlákien)" % cores if cores else ""))
    for line in _read(root, "proc/meminfo").splitlines():
        if line.startswith("MemTotal:"):
            kib = int(line.split()[1])
            items.append(Item("computer", "memory", "Operačná pamäť", ("%.1f GB" % (kib / 1024 / 1024)).replace(".", ",")))
            break
    return items


def read_pci(root, lspci_text):
    """(grafika, čipset a radiče, {slot: info}) z PCI; sieť a zvuk sa tu nebrali (majú vlastnú skupinu)."""
    infos = parse_lspci(lspci_text)
    graphics, platform = [], []
    for slot, info in sorted(infos.items()):
        cls = info["class"]
        name = pci_title(info)
        if cls.startswith("03"):
            driver = os.path.basename(os.path.realpath(_path(root, "sys/bus/pci/devices", slot, "driver")))
            graphics.append(Item("graphics", slot, name, "%s · ovládač %s" % (info["class_name"], driver)
                                 if driver and driver != "driver" else info["class_name"]))
        elif cls not in PCI_COVERED:
            platform.append(Item("platform", slot, name, info["class_name"]))
    return graphics, platform, infos


def read_audio(root):
    items = []
    lines = _read(root, "proc/asound/cards").splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^\s*(\d+) \[(\S+)\s*\]:\s*(\S+) - (.+)$", line)
        if m:
            detail = lines[i + 1].strip() if i + 1 < len(lines) and not re.match(r"^\s*\d+ \[", lines[i + 1]) else ""
            items.append(Item("audio", "card" + m.group(1), m.group(4).strip(), detail))
    return items


def read_network(root, pci):
    items = []
    for name in _listdir(root, "sys/class/net"):
        base = _path(root, "sys/class/net", name)
        if name == "lo" or "/virtual/" in os.path.realpath(base):
            continue                                  # spätná slučka a virtuálne rozhrania nie sú hardvér
        wireless = os.path.isdir(os.path.join(base, "wireless")) or os.path.isdir(os.path.join(base, "phy80211"))
        slot = os.path.basename(os.path.realpath(os.path.join(base, "device")))
        info = pci.get(slot)
        oper = _read(root, "sys/class/net", name, "operstate")
        kind = "Wi-Fi" if wireless else "Ethernet"
        items.append(Item("network", name, pci_title(info) if info else name,
                          "%s · rozhranie %s" % (kind, name),
                          {"up": "pripojené", "down": "nepripojené"}.get(oper, oper),
                          {"wireless": wireless}))
    return items


INPUT_BLOCK = re.compile(r'^N: Name="(.*)"$', re.M)


def parse_input(text):
    """[{"name", "handlers", "ev", "prop"}] z /proc/bus/input/devices."""
    devices = []
    for block in re.split(r"\n\s*\n", text.strip()):
        name = INPUT_BLOCK.search(block)
        handlers = re.search(r"^H: Handlers=(.*)$", block, re.M)
        ev = re.search(r"^B: EV=([0-9a-f]+)", block, re.M)
        prop = re.search(r"^B: PROP=([0-9a-f]+)", block, re.M)
        if name:
            devices.append({"name": name.group(1), "handlers": handlers.group(1).split() if handlers else [],
                            "ev": int(ev.group(1), 16) if ev else 0, "prop": int(prop.group(1), 16) if prop else 0})
    return devices


def classify_input(dev):
    """Druh vstupného zariadenia, alebo None pre systémové tlačidlá a pseudozariadenia."""
    low = dev["name"].lower()
    if any(low.startswith(s) or low == s.strip() for s in SYSTEM_INPUTS):
        return None
    if "touchpad" in low or "trackpad" in low:
        return "Touchpad"
    if "touchscreen" in low or "touch screen" in low:
        return "Dotyková obrazovka"
    if "gamepad" in low or "controller" in low or "joystick" in low:
        return "Ovládač hier"
    if "tablet" in low:
        return "Tablet"
    handlers = dev["handlers"]
    if "mouse" in " ".join(handlers):
        return "Myš"
    if "kbd" in handlers and dev["ev"] & 0x100000:      # EV_REP: klávesnica opakuje klávesy
        return "Klávesnica"
    return None


def read_input(root):
    items = []
    for i, dev in enumerate(parse_input(_read(root, "proc/bus/input/devices"))):
        kind = classify_input(dev)
        if kind:
            items.append(Item("input", "input%d-%s" % (i, dev["name"]), dev["name"], kind, "", {"kind": kind}))
    return items


def _usb_interfaces(root, dev):
    base = _path(root, "sys/bus/usb/devices", dev)
    return sorted({_read(root, "sys/bus/usb/devices", dev, entry, "bInterfaceClass").lower()
                   for entry in _listdir(root, "sys/bus/usb/devices", dev) if entry.startswith(dev + ":")
                   if os.path.isdir(os.path.join(base, entry))} - {""})


def read_usb(root):
    items = []
    for dev in _listdir(root, "sys/bus/usb/devices"):
        if ":" in dev or dev.startswith("usb"):
            continue                                     # rozhrania a koreňové rozbočovače
        product = _read(root, "sys/bus/usb/devices", dev, "product")
        if not product:
            continue
        classes = set(_usb_interfaces(root, dev))
        dclass = _read(root, "sys/bus/usb/devices", dev, "bDeviceClass").lower()
        if dclass and dclass != "00":
            classes.add(dclass)
        if classes and classes <= USB_COVERED:
            continue                                     # klávesnica, disk, kamera... sú vo svojej skupine
        maker = _read(root, "sys/bus/usb/devices", dev, "manufacturer")
        items.append(Item("usb", dev, product, "výrobca %s" % maker if maker else "", "pripojené"))
    return items


def read_lsblk(text):
    """Disky z `lsblk -dJ`: celé zariadenia, nie oddiely."""
    items = []
    for node in json.loads(text).get("blockdevices", []):
        name = node.get("name", "")
        if node.get("type") not in ("disk", "rom") or re.match(r"^(loop|ram|zram|nbd|fd)", name):
            continue
        maker, model = (node.get("vendor") or "").strip(), (node.get("model") or "").strip()
        title = " ".join(x for x in (maker, model) if x) or "/dev/" + name
        bus = {"sata": "SATA", "usb": "USB", "nvme": "NVMe", "ata": "ATA"}.get(node.get("tran") or "", (node.get("tran") or "").upper())
        if node.get("type") == "rom":
            group, kind, kind_text = "optical", "optical", "Optická mechanika"
        elif bus == "USB":
            group, kind, kind_text = "storage", "usb", "USB disk"
        elif node.get("rota") in (False, 0, "0"):
            group, kind, kind_text = "storage", "ssd", "SSD"
        else:
            group, kind, kind_text = "storage", "hdd", "Pevný disk"
        detail = " · ".join(x for x in (kind_text, node.get("size") or "", bus, "/dev/" + name) if x)
        items.append(Item(group, name, title, detail, "", {"kind": kind}))
    return items


NM_TYPES = {"802-3-ethernet": "Kábel", "802-11-wireless": "Wi-Fi", "vpn": "VPN", "wireguard": "WireGuard",
            "gsm": "Mobilná sieť", "cdma": "Mobilná sieť", "bluetooth": "Bluetooth", "pppoe": "PPPoE",
            "wimax": "WiMAX", "infiniband": "InfiniBand"}
NM_VPN = {"vpn", "wireguard"}


def split_nmcli(line):
    """Polia riadku `nmcli -t`: dvojbodka je oddeľovač, „\\:“ je dvojbodka v hodnote."""
    fields, current, i = [], "", 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line):
            current += line[i + 1]
            i += 2
            continue
        if ch == ":":
            fields.append(current)
            current = ""
        else:
            current += ch
        i += 1
    fields.append(current)
    return fields


def read_connections(text):
    """Uložené pripojenia a VPN z `nmcli -t -f NAME,TYPE,DEVICE,STATE connection show`.

    Virtuálne siete (spätná slučka, mosty, veth, tunely kontajnerov) nie sú pripojenia používateľa.
    """
    items = []
    for line in text.splitlines():
        fields = split_nmcli(line)
        if len(fields) < 3 or not fields[0]:
            continue
        name, kind, device = fields[0], fields[1], fields[2]
        state = fields[3] if len(fields) > 3 else ""
        if kind not in NM_TYPES:
            continue
        status = {"activated": "pripojené", "activating": "pripája sa"}.get(state, "" if state == "" and device else "nepripojené")
        detail = " · ".join(x for x in (NM_TYPES[kind], device) if x)
        items.append(Item("vpn" if kind in NM_VPN else "connection", name, name, detail, status,
                          {"wireless": kind == "802-11-wireless", "type": kind}))
    return items


def read_power(root):
    items = []
    for name in _listdir(root, "sys/class/power_supply"):
        kind = _read(root, "sys/class/power_supply", name, "type")
        if kind == "Battery":
            capacity = _read(root, "sys/class/power_supply", name, "capacity")
            status = _read(root, "sys/class/power_supply", name, "status")
            model = _read(root, "sys/class/power_supply", name, "model_name")
            items.append(Item("power", name, model or "Batéria", "%s %%" % capacity if capacity else "", status,
                              {"battery": True}))
        elif kind == "Mains":
            online = _read(root, "sys/class/power_supply", name, "online") == "1"
            items.append(Item("power", name, "Sieťové napájanie", "", "pripojené" if online else "nepripojené"))
    return sorted(items, key=lambda i: not i.extra.get("battery"))          # batéria prvá, zásuvka za ňou


def read_cameras(root):
    items = []
    for name in _listdir(root, "sys/class/video4linux"):
        if _read(root, "sys/class/video4linux", name, "index") not in ("", "0"):
            continue                                     # druhý uzol tej istej kamery (metadáta)
        title = _read(root, "sys/class/video4linux", name, "name")
        if title:
            items.append(Item("camera", name, title, "/dev/" + name))
    return items


def read_bluetooth(root):
    items = []
    for name in _listdir(root, "sys/class/bluetooth"):
        if ":" in name:
            continue                                     # pripojené zariadenia, nie adaptér
        items.append(Item("bluetooth", name, "Bluetooth adaptér", name, ""))
    return items


def read_displays(heads):
    items = []
    for ident, head in sorted(displays.identify(heads).items(), key=lambda kv: kv[1].id):
        size = displays.diagonal_inches(head)
        detail = " · ".join(x for x in (displays.summary(head), "%.0f″" % size if size else "", head.name) if x)
        items.append(Item("display", ident, displays.title(head), detail,
                          "zapnutý" if head.enabled else "vypnutý", {"connector": head.name}))
    return items


def read_drm(root):
    """Náhradný zdroj monitorov, keď kompozitor neodpovedá: pripojené konektory z DRM (bez rozlíšení)."""
    items = []
    for name in _listdir(root, "sys/class/drm"):
        if re.match(r"^card\d+-", name) and _read(root, "sys/class/drm", name, "status") == "connected":
            connector = name.split("-", 1)[1]
            items.append(Item("display", connector.lower(), connector, "konektor %s · bez údajov od kompozitora" % connector,
                              "pripojený", {"connector": connector}))
    return items


# ---------------------------------------------------------------- skenovanie
def scan(root="/", heads=None, run=run_command):
    """Celý inventár. heads=None: monitory sa spýtajú kompozitora. run: príkaz -> text (výmena v testoch)."""
    inv = Inventory()

    def guard(label, fn):
        try:
            return fn()
        except (OSError, ValueError, KeyError, outputs.OutputsError) as err:
            inv.problems.append("%s: %s" % (label, err))
            return None

    inv.items += read_computer(root)

    lspci = guard("PCI zariadenia (lspci)", lambda: run(["lspci", "-mm", "-nn"])) or ""
    graphics, platform, pci = read_pci(root, lspci)
    if not lspci:
        inv.problems.append("Názvy grafiky a radičov nie sú, chýba lspci (balík pciutils).")

    if heads is None:
        heads = guard("Monitory (kompozitor)", outputs.read)
    if heads is not None:
        inv.items += read_displays(heads)
    else:
        inv.items += read_drm(root)
    inv.items += graphics
    inv.items += read_audio(root)
    inv.items += read_network(root, pci)
    inv.items += read_input(root)
    inv.items += read_cameras(root)
    inv.items += read_bluetooth(root)
    connections = guard("Pripojenia (nmcli)", lambda: read_connections(
        run(["nmcli", "-t", "-f", "NAME,TYPE,DEVICE,STATE", "connection", "show"])))
    inv.items += connections or []
    disks = guard("Disky (lsblk)", lambda: read_lsblk(run(["lsblk", "-dJ", "-o", "NAME,TYPE,SIZE,MODEL,VENDOR,TRAN,ROTA"])))
    inv.items += disks or []
    inv.items += read_usb(root)
    inv.items += read_power(root)
    inv.items += platform
    return inv
