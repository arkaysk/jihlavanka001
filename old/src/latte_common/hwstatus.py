"""Stav hardvéru podľa zariadenia: funguje / chýba firmvér / chýba balík / treba repozitár / nepodporované.

Roadmapa, bod H.2. Samostatný modul, aby zisťovanie hardvéru (hardware.py) zostalo len na čítanie
a nezačalo riešiť balíky. Tento modul tiež nič nemení a nič neinštaluje; vie iba povedať, čo chýba
a ktorým balíkom sa to doplní. Doplnenie patrí do bodu H.7.

Zdroje (všetky lokálne, bez siete):
    sysfs       `/sys/bus/pci/devices/<slot>/driver` — je na zariadenie naviazaný ovládač?
    jadro       záznam o neúspešnom načítaní firmvéru (journalctl -k, inak dmesg)
    rpm         cez hwbase.py: ktorý balík zo zoznamu `latteos-base` chýba

Zásada 6: čo sa nedá zistiť, sa povie. Ak nie je čitateľný záznam jadra, chýbajúci firmvér sa
nehlási ako „funguje“, ale ako `unknown` a dôvod je v `problems`.

Zariadenia, ktoré sa neprihlásili v žiadnej skupine, drží skupina **Ostatné zariadenia**
(hardware.read_unclaimed_pci). Tento modul im k tomu dá dôvod: chýba balík, chýba firmvér, alebo
jadro pre ne ovládač nemá. Nezaradené zariadenie je vždy „niečo na vyriešenie“, nikdy nie „ok“:
bez ovládača nefunguje, aj keď na zbernici je.
"""
import os
import re
from dataclasses import dataclass, field

from latte_common import hardware, hwbase

STATES = ("ok", "firmware", "package", "repo", "unsupported", "unknown")
STATE_TITLES = {
    "ok": "funguje",
    "firmware": "chýba firmvér",
    "package": "chýba balík",
    "repo": "treba cudzí repozitár",
    "unsupported": "nepodporované",
    "unknown": "nezistené",
}
# Pre používateľa dôležité poradie: najprv to, čo nefunguje.
STATE_ORDER = {"firmware": 0, "package": 1, "repo": 2, "unsupported": 3, "unknown": 4, "ok": 5}

# Trieda PCI -> skupina balíkov, ktorá sa o také zariadenie stará (pri nezaradených zariadeniach).
PCI_CLASS_GROUPS = {"03": "graphics", "0200": "network", "0280": "network", "0401": "audio", "0403": "audio"}
# Mosty a zbernice (trieda 06xx) ovládač nepotrebujú; bez tohto by ich Správca hlásil ako nepodporované.
NO_DRIVER_NEEDED = ("06",)

# Hardvér, pre ktorý vo Fedore ovládač nie je a je len v cudzom repozitári. Zámerne krátky zoznam:
# pre drvivú väčšinu hardvéru (AMD, Intel, Realtek, MediaTek, Qualcomm...) stačí Fedora a nič sem
# nepatrí. Kľúč je (výrobca, trieda PCI alebo jej prvé dva znaky).
NEEDS_REPO = {
    ("10de", "03"): ("rpmfusion-nonfree", ("akmod-nvidia", "xorg-x11-drv-nvidia-cuda"),
                     "Karta NVIDIA nemá ovládač. Otvorený nouveau nie je načítaný a proprietárny je "
                     "v RPM Fusion Nonfree, ktorý sa zapína len s tvojím súhlasom."),
    ("14e4", "0280"): ("rpmfusion-nonfree", ("broadcom-wl",),
                       "Wi-Fi Broadcom. Fedora preň ovládač nemá a slobodná náhrada (b43, brcmfmac) "
                       "túto kartu nepodporuje; broadcom-wl je v RPM Fusion Nonfree."),
}


@dataclass
class Status:
    key: str                        # identita v rámci skupiny (slot PCI, meno rozhrania...)
    group: str                      # skupina zo hardware.GROUPS
    name: str
    state: str = "ok"
    reason: str = ""                # jedna veta pre používateľa
    packages: tuple = ()            # čím sa to doplní
    repo: str = ""                  # repozitár, ktorý treba najprv zapnúť
    unclaimed: bool = False         # zariadenie je na zbernici, ale neprihlásilo sa v žiadnej skupine

    @property
    def title(self):
        return STATE_TITLES[self.state]

    @property
    def ok(self):
        return self.state == "ok"


@dataclass
class Report:
    statuses: list = field(default_factory=list)
    problems: list = field(default_factory=list)

    def by_state(self, *states):
        return [s for s in self.statuses if s.state in states]

    def for_item(self, group, key):
        for status in self.statuses:
            if status.group == group and status.key == key:
                return status
        return None

    @property
    def faults(self):
        """Všetko, čo nefunguje alebo sa nedalo zistiť, v poradí naliehavosti."""
        return sorted((s for s in self.statuses if not s.ok), key=lambda s: (STATE_ORDER[s.state], s.group, s.name))

    def summary(self):
        faults = self.faults
        if not faults and self.problems:
            return "Hardvér vyzerá v poriadku, ale nie všetko sa dalo overiť."
        if not faults:
            return "Všetok nájdený hardvér má ovládač aj firmvér."
        return "Pozornosť si žiada %d z %d zariadení." % (len(faults), len(self.statuses))


# ---------------------------------------------------------------- záznam jadra
# iwlwifi 0000:00:14.3: Direct firmware load for iwlwifi-...ucode failed with error -2
DIRECT_LOAD = re.compile(
    r"(?P<driver>[\w.\-]+)\s+(?P<device>[\w:.\-]+):\s+Direct firmware load for\s+(?P<file>\S+)\s+failed")
# firmware: failed to load amdgpu/xyz.bin (-2)
FAILED_LOAD = re.compile(r"firmware:\s+failed to load\s+(?P<file>\S+)\s+\(")


def parse_firmware_failures(text):
    """{identita zariadenia alebo ovládača: (súbory firmvéru)} z textu záznamu jadra.

    Kľúčom je slot PCI („0000:00:14.3“), ak ho riadok nesie, inak meno ovládača. Obe sa hľadajú,
    lebo nie každý ovládač píše slot."""
    found = {}
    for line in text.splitlines():
        match = DIRECT_LOAD.search(line)
        if match:
            for key in (match.group("device"), match.group("driver")):
                found.setdefault(key, [])
                if match.group("file") not in found[key]:
                    found[key].append(match.group("file"))
            continue
        match = FAILED_LOAD.search(line)
        if match:
            found.setdefault("", [])
            if match.group("file") not in found[""]:
                found[""].append(match.group("file"))
    return {key: tuple(files) for key, files in found.items()}


def read_kernel_log(run=hardware.run_command):
    """Záznam jadra od štartu. OSError, keď sa nedá prečítať (dmesg býva pre používateľa zakázaný)."""
    try:
        return run(["journalctl", "-k", "-b", "--no-pager", "-o", "cat"])
    except OSError:
        return run(["dmesg"])


# ---------------------------------------------------------------- sysfs
def pci_driver(root, slot):
    """Meno ovládača naviazaného na PCI zariadenie, alebo prázdny reťazec."""
    link = os.path.join(root, "sys/bus/pci/devices", slot, "driver")
    if not os.path.islink(link):
        return ""
    return os.path.basename(os.path.realpath(link))


def pci_class(root, slot):
    """Trieda PCI ako štyri znaky („0300“ grafika, „0601“ ISA most), alebo prázdny reťazec."""
    try:
        with open(os.path.join(root, "sys/bus/pci/devices", slot, "class"), encoding="utf-8") as stream:
            return stream.read().strip().lower().replace("0x", "").zfill(6)[:4]
    except OSError:
        return ""


def pci_ids(root, slot):
    """(vendor, device) ako štvorznakové id bez predpony 0x."""
    def read(name):
        try:
            with open(os.path.join(root, "sys/bus/pci/devices", slot, name), encoding="utf-8") as stream:
                return stream.read().strip().lower().replace("0x", "")
        except OSError:
            return ""
    return read("vendor"), read("device")


def net_slot(root, name):
    """Slot PCI sieťového rozhrania, alebo prázdny reťazec (USB a virtuálne rozhrania ho nemajú)."""
    link = os.path.join(root, "sys/class/net", name, "device")
    if not os.path.exists(link):
        return ""
    base = os.path.basename(os.path.realpath(link))
    return base if re.match(r"^[0-9a-f]{4}:", base) else ""


# ---------------------------------------------------------------- vyhodnotenie
def _missing_required(base, group_id):
    """Povinné balíky, ktoré na tomto stroji chýbajú, zo skupín starajúcich sa o dané zariadenia."""
    if base is None:
        return ()
    out = []
    for group in base.plan.for_device_group(group_id):
        out += [p for p in group.required() if base.state(p.name) in ("missing", "repo")]
    return tuple(out)


def _package_status(status, base, group_id, reason):
    """Ak skupine chýba povinný balík, stav je 'package' (alebo 'repo'), inak sa nemení."""
    missing = _missing_required(base, group_id)
    if not missing:
        return status
    status.state = "repo" if all(base.state(p.name) == "repo" for p in missing) else "package"
    status.packages = tuple(p.name for p in missing)
    status.repo = next((p.repo for p in missing if p.repo), "")
    status.reason = reason % ", ".join(status.packages)
    return status


def _firmware_keys(status_key, slot, driver):
    return tuple(k for k in (slot, driver, status_key) if k)


def _apply_firmware(status, failures, *keys):
    """Ak jadro pre zariadenie hlásilo neúspešné načítanie firmvéru, stav je 'firmware'."""
    for key in keys:
        files = failures.get(key)
        if files:
            status.state = "firmware"
            status.reason = "Jadro nenačítalo firmvér: %s." % ", ".join(files)
            status.packages = ("linux-firmware",)
            return status
    return status


def evaluate(inv, root="/", base=None, log=None, run=hardware.run_command):
    """Report pre celý inventár. `base` je hwbase.Report (None = zistí sa), `log` text záznamu jadra."""
    report = Report()
    if base is None:
        try:
            base = hwbase.check(root=root)
        except hwbase.BaseError as err:
            report.problems.append("Zoznam balíkov latteos-base: %s" % err)
    if base is not None:
        report.problems += list(base.problems)

    failures, known_firmware = {}, True
    if log is None:
        try:
            log = read_kernel_log(run)
        except OSError as err:
            known_firmware = False
            report.problems.append("Záznam jadra sa nedá čítať (%s); chýbajúci firmvér sa nedá overiť." % err)
    if log is not None:
        failures = parse_firmware_failures(log)

    for item in inv.items:
        status = _evaluate_item(item, root, base, failures, known_firmware)
        if status is not None:
            report.statuses.append(status)
    return report


def _evaluate_item(item, root, base, failures, known_firmware):
    group = item.group
    if group in ("connection", "vpn"):
        return None                                  # uložené pripojenie nie je zariadenie
    status = Status(item.key, group, item.name, "ok", "")

    if group == "other":
        return _evaluate_unclaimed(status, item, root, base, failures, known_firmware)

    if group in ("graphics", "platform"):
        slot = item.key
        driver = pci_driver(root, slot)
        if driver:
            status.reason = "Ovládač %s." % driver
            _apply_firmware(status, failures, slot, driver)
            if status.ok and group == "graphics":
                _package_status(status, base, "graphics", "Ovládač beží, ale chýba %s.")
            return status
        return _no_driver(status, root, slot, base, group)

    if group == "network":
        slot = item.extra.get("slot") or net_slot(root, item.key)
        driver = pci_driver(root, slot) if slot else ""
        status.reason = "Rozhranie %s%s." % (item.key, ", ovládač %s" % driver if driver else "")
        _apply_firmware(status, failures, *_firmware_keys("", slot, driver))
        if status.ok:
            _package_status(status, base, "network", "Karta funguje, ale chýba %s.")
        return status

    if group == "audio":
        slot = item.extra.get("slot", "")
        driver = pci_driver(root, slot) if slot else ""
        _apply_firmware(status, failures, *_firmware_keys("", slot, driver))
        if status.ok:
            _package_status(status, base, "audio", "Karta je nájdená, ale chýba %s.")
        return status

    if group == "input":
        if item.extra.get("kind") == "Tablet":
            _package_status(status, base, "input", "Tablet potrebuje %s.")
        return status

    if group == "bluetooth":
        _apply_firmware(status, failures, "bluetooth", "btusb")
        if status.ok:
            _package_status(status, base, "bluetooth", "Adaptér je nájdený, ale chýba %s.")
        return status

    if group in ("storage", "optical"):
        _package_status(status, base, "storage", "Disk je nájdený, ale chýba %s.")
        return status

    if group == "power":
        _package_status(status, base, "power", "Napájanie sa číta, ale chýba %s.")
        return status

    if group == "usb":
        return status

    if group == "display":
        status.reason = "Monitor je %s." % (item.status or "pripojený")
        return status

    if group == "computer" and not known_firmware:
        status.state = "unknown"
        status.reason = "Záznam jadra nie je čitateľný, firmvér sa nedá overiť."
    return status


def _no_driver(status, root, slot, base, group):
    """PCI zariadenie bez naviazaného ovládača: čím sa to dá vyriešiť, alebo poctivé „nepodporované“."""
    if pci_class(root, slot).startswith(NO_DRIVER_NEEDED):
        status.reason = "Most alebo zbernica; ovládač nepotrebuje."
        return status
    vendor, _device = pci_ids(root, slot)
    cls = pci_class(root, slot)
    known = NEEDS_REPO.get((vendor, cls)) or NEEDS_REPO.get((vendor, cls[:2]))
    if known:
        status.repo, status.packages, status.reason = known
        status.state = "repo"
        return status
    missing = _missing_required(base, group)
    if missing:
        status.state = "repo" if all(base.state(p.name) == "repo" for p in missing) else "package"
        status.packages = tuple(p.name for p in missing)
        status.repo = next((p.repo for p in missing if p.repo), "")
        status.reason = "Zariadenie nemá ovládač a chýba %s." % ", ".join(status.packages)
        return status
    status.state = "unsupported"
    status.reason = "Jadro pre toto zariadenie nemá ovládač a v zozname latteos-base nič nechýba."
    return status


def _evaluate_unclaimed(status, item, root, base, failures, known_firmware):
    """Zariadenie zo skupiny Ostatné: je na zbernici, ale nikde sa neprihlásilo. Nikdy nie je „ok“ —
    buď sa dá povedať, čo chýba, alebo sa poctivo povie, že sa to nedá zistiť."""
    status.unclaimed = True
    slot = item.extra.get("slot")
    if not slot:                                     # USB zariadenie, ktoré nepovedalo, čo je
        status.state = "unknown"
        status.reason = ("Zariadenie sa ohlásilo, ale nepovedalo, čo je (%s). Jadro mu ovládač "
                         "nepriradilo alebo ho nepotrebuje." % (item.extra.get("usb_id") or "bez id"))
        return status
    _apply_firmware(status, failures, slot, item.extra.get("driver", ""))
    if not status.ok:
        status.reason = "Zariadenie sa neprihlásilo do žiadnej skupiny. " + status.reason
        return status
    cls = item.extra.get("class", "")
    group = PCI_CLASS_GROUPS.get(cls) or PCI_CLASS_GROUPS.get(cls[:2]) or "graphics"
    if item.extra.get("driver"):
        status.state = "unknown"
        status.reason = ("Ovládač %s je naviazaný, ale zariadenie nevytvorilo rozhranie. "
                         "Dôvod sa z dostupných zdrojov zistiť nedá." % item.extra["driver"])
        return status
    _no_driver(status, root, slot, base, group)
    status.reason = "Bez ovládača nevytvorí rozhranie, preto nie je vo svojej skupine. " + status.reason
    return status
