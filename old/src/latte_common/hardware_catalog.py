"""Offline identifikacia PCI hardware pre Proces Manager/Monitor.

Zdroje sa citaju lokalne v tomto poradi: systemovy hwdata/pci.ids a pribaleny
LatteOS katalog. Siet nie je podmienkou pre zobrazenie aktualneho stavu.
"""
import os
from dataclasses import dataclass, field

from latte_common import paths


@dataclass
class Catalog:
    source: str = ""
    vendors: dict = field(default_factory=dict)
    devices: dict = field(default_factory=dict)

    @property
    def loaded(self):
        return bool(self.vendors or self.devices)

    def vendor_name(self, vendor):
        return self.vendors.get(vendor.lower(), vendor)

    def device_name(self, vendor, device):
        return self.devices.get((vendor.lower(), device.lower()), device)

    def identify(self, vendor, device):
        return "%s %s" % (self.vendor_name(vendor), self.device_name(vendor, device))


def _sources(data_dir=None):
    explicit = data_dir is not None
    data_dir = data_dir or paths.data_dir()
    bundled = os.path.join(data_dir, "hardware", "pci.ids")
    system = (
        "/usr/share/hwdata/pci.ids",
        "/usr/share/misc/pci.ids",
    )
    return (bundled,) + system if explicit else system + (bundled,)


def load(data_dir=None):
    catalog = Catalog()
    for source in _sources(data_dir):
        if not os.path.isfile(source):
            continue
        _parse(source, catalog)
        catalog.source = source
        break
    return catalog


def _parse(source, catalog):
    vendor = None
    try:
        with open(source, encoding="utf-8", errors="replace") as stream:
            for line in stream:
                if not line.strip() or line.startswith("#"):
                    continue
                if line[0].isspace():
                    if vendor and not line.startswith("\t\t"):
                        parts = line.strip().split(None, 1)
                        if len(parts) == 2 and len(parts[0]) == 4:
                            catalog.devices[(vendor, parts[0].lower())] = parts[1].strip()
                    continue
                parts = line.strip().split(None, 1)
                if len(parts) == 2 and len(parts[0]) == 4:
                    vendor = parts[0].lower()
                    catalog.vendors[vendor] = parts[1].strip()
    except OSError:
        return


def update_sources():
    """Vrati dostupny lokalny zdroj aktualizacie bez jeho automatickeho spustenia.

    Samotne stiahnutie patri systemovemu update mechanizmu alebo neskorsiemu
    LatteOS updateru. Monitor pri tom zostava funkcny aj so starym katalogom.
    """
    return {
        "package": "pci.ids / hwdata",
        "paths": list(_sources()),
        "offline": True,
        "note": "Katalog sa aktualizuje spolu so systemovym balikom hwdata alebo pciutils-ids.",
    }
