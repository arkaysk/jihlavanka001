import os
import sys
import tempfile
import tomllib
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import hardware, hwbase, hwstatus  # noqa: E402

PLAN_TOML = """
[base]
id = "latteos-base"

[repo.rpmfusion-nonfree]
title = "RPM Fusion Nonfree"
note = "Proprietárne."

[[group]]
id = "graphics"
title = "Grafika"
why = "3D."
devices = ["graphics"]
required = ["mesa-dri-drivers"]

[[group]]
id = "audio"
title = "Zvuk"
why = "Zvuk."
devices = ["audio"]
required = ["pipewire"]

[[group]]
id = "bluetooth"
title = "Bluetooth"
why = "BT."
devices = ["bluetooth"]
required = ["bluez"]
"""

LOG = """\
kernel: iwlwifi 0000:04:00.0: Direct firmware load for iwlwifi-so-a0-gf-a0-83.ucode failed with error -2
kernel: iwlwifi 0000:04:00.0: Direct firmware load for iwlwifi-so-a0-gf-a0-82.ucode failed with error -2
kernel: platform regulatory.0: Direct firmware load for regulatory.db failed with error -2
kernel: firmware: failed to load amdgpu/pekny.bin (-2)
kernel: e1000: enp0s3 NIC Link is Up
"""


def fake_base(installed_names, repos=("fedora",)):
    """hwbase.Report nad malým plánom: `installed_names` je, čo je na stroji nainštalované."""
    plan = hwbase.parse(tomllib.loads(PLAN_TOML), "skúška")
    report = hwbase.Report(plan, repos=frozenset(repos))
    for package in plan.packages():
        if package.name in installed_names:
            report.states[package.name] = "installed"
        elif package.repo and package.repo not in report.repos:
            report.states[package.name] = "repo"
        else:
            report.states[package.name] = "missing"
    return report


def write(root, relative, text):
    path = os.path.join(root, relative.lstrip("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as stream:
        stream.write(text)


def pci_device(root, slot, vendor="8086", device="1234", cls="030000", driver=None):
    base = "sys/bus/pci/devices/%s" % slot
    write(root, base + "/vendor", "0x%s\n" % vendor)
    write(root, base + "/device", "0x%s\n" % device)
    write(root, base + "/class", "0x%s\n" % cls)
    if driver:
        target = os.path.join(root, "sys/bus/pci/drivers", driver)
        os.makedirs(target, exist_ok=True)
        os.symlink(target, os.path.join(root, base, "driver"))


class FirmwareLog(unittest.TestCase):
    def test_direct_load_keyed_by_slot_and_driver(self):
        found = hwstatus.parse_firmware_failures(LOG)
        self.assertEqual(found["0000:04:00.0"],
                         ("iwlwifi-so-a0-gf-a0-83.ucode", "iwlwifi-so-a0-gf-a0-82.ucode"))
        self.assertIn("iwlwifi", found)
        self.assertIn("regulatory.0", found)

    def test_plain_failed_to_load(self):
        self.assertEqual(hwstatus.parse_firmware_failures(LOG)[""], ("amdgpu/pekny.bin",))

    def test_healthy_log_has_nothing(self):
        self.assertEqual(hwstatus.parse_firmware_failures("kernel: e1000: link up\n"), {})

    def test_reader_falls_back_to_dmesg(self):
        calls = []

        def run(argv):
            calls.append(argv[0])
            if argv[0] == "journalctl":
                raise OSError("nie je dovolené")
            return "text"
        self.assertEqual(hwstatus.read_kernel_log(run), "text")
        self.assertEqual(calls, ["journalctl", "dmesg"])

    def test_reader_raises_when_neither_works(self):
        def run(_argv):
            raise OSError("zakázané")
        with self.assertRaises(OSError):
            hwstatus.read_kernel_log(run)


class Sysfs(unittest.TestCase):
    def test_driver_class_and_ids(self):
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:01:00.0", vendor="10de", device="2504", cls="030000", driver="nouveau")
            pci_device(root, "0000:00:1f.3", cls="040300")
            self.assertEqual(hwstatus.pci_driver(root, "0000:01:00.0"), "nouveau")
            self.assertEqual(hwstatus.pci_driver(root, "0000:00:1f.3"), "")
            self.assertEqual(hwstatus.pci_ids(root, "0000:01:00.0"), ("10de", "2504"))
            self.assertEqual(hwstatus.pci_class(root, "0000:00:1f.3"), "0403")

    def test_net_slot_only_for_pci(self):
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:03:00.0", cls="020000", driver="e1000e")
            os.makedirs(os.path.join(root, "sys/class/net/enp3s0"))
            os.symlink(os.path.join(root, "sys/bus/pci/devices/0000:03:00.0"),
                       os.path.join(root, "sys/class/net/enp3s0/device"))
            self.assertEqual(hwstatus.net_slot(root, "enp3s0"), "0000:03:00.0")
            os.makedirs(os.path.join(root, "sys/class/net/lo"))
            self.assertEqual(hwstatus.net_slot(root, "lo"), "")


def no_lspci(argv):
    raise OSError("%s: nie je" % argv[0])


class Evaluate(unittest.TestCase):
    """Vyhodnotenie beží nad falošným sysfs, aby nezáviselo od stroja, na ktorom sa skúša."""

    def evaluate(self, root, items, base=None, log=""):
        inv = hardware.Inventory(items=list(items))
        return hwstatus.evaluate(inv, root=root, base=base or fake_base(["mesa-dri-drivers", "pipewire", "bluez"]),
                                 log=log, run=no_lspci)

    def test_graphics_with_driver_is_ok(self):
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:01:00.0", driver="amdgpu")
            report = self.evaluate(root, [hardware.Item("graphics", "0000:01:00.0", "AMD Radeon")])
        status = report.statuses[0]
        self.assertEqual(status.state, "ok")
        self.assertIn("amdgpu", status.reason)
        self.assertIn("ovládač aj firmvér", report.summary())

    def test_nvidia_without_driver_needs_repo(self):
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:01:00.0", vendor="10de", cls="030000")
            report = self.evaluate(root, [hardware.Item("graphics", "0000:01:00.0", "NVIDIA GeForce")])
        status = report.statuses[0]
        self.assertEqual(status.state, "repo")
        self.assertEqual(status.repo, "rpmfusion-nonfree")
        self.assertIn("akmod-nvidia", status.packages)

    def test_graphics_without_driver_and_without_mesa_names_the_package(self):
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:01:00.0", vendor="8086", cls="030000")
            report = self.evaluate(root, [hardware.Item("graphics", "0000:01:00.0", "Intel Graphics")],
                                   base=fake_base(["pipewire", "bluez"]))
        status = report.statuses[0]
        self.assertEqual(status.state, "package")
        self.assertEqual(status.packages, ("mesa-dri-drivers",))

    def test_unknown_device_without_driver_is_unsupported_not_ok(self):
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:02:00.0", cls="0c0330")
            report = self.evaluate(root, [hardware.Item("platform", "0000:02:00.0", "USB radič")])
        self.assertEqual(report.statuses[0].state, "unsupported")

    def test_broadcom_wifi_without_driver_points_to_the_repo(self):
        """Nie je to len o NVIDII: pravidlo je tabuľka (výrobca, trieda), nie jeden špeciálny prípad."""
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:03:00.0", vendor="14e4", cls="028000")
            report = self.evaluate(root, [hardware.Item("platform", "0000:03:00.0", "Broadcom BCM4360")])
        status = report.statuses[0]
        self.assertEqual(status.state, "repo")
        self.assertEqual(status.packages, ("broadcom-wl",))
        self.assertEqual(status.repo, "rpmfusion-nonfree")

    def test_common_vendor_without_driver_is_not_sent_to_a_third_party_repo(self):
        """Pre AMD, Intel, Realtek a spol. cudzí repozitár netreba a nesmie sa ponúkať."""
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:03:00.0", vendor="10ec", cls="020000")
            report = self.evaluate(root, [hardware.Item("platform", "0000:03:00.0", "Realtek RTL8168")])
        self.assertNotEqual(report.statuses[0].state, "repo")
        self.assertEqual(report.statuses[0].repo, "")

    def test_bridge_does_not_need_a_driver(self):
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:00:00.0", cls="060000")
            report = self.evaluate(root, [hardware.Item("platform", "0000:00:00.0", "Host bridge")])
        self.assertEqual(report.statuses[0].state, "ok")
        self.assertIn("Most", report.statuses[0].reason)

    def test_firmware_failure_wins_over_bound_driver(self):
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:04:00.0", cls="028000", driver="iwlwifi")
            os.makedirs(os.path.join(root, "sys/class/net/wlp4s0"))
            os.symlink(os.path.join(root, "sys/bus/pci/devices/0000:04:00.0"),
                       os.path.join(root, "sys/class/net/wlp4s0/device"))
            report = self.evaluate(root, [hardware.Item("network", "wlp4s0", "Intel Wi-Fi 6E")], log=LOG)
        status = report.statuses[0]
        self.assertEqual(status.state, "firmware")
        self.assertIn("iwlwifi-so-a0-gf-a0-83.ucode", status.reason)
        self.assertEqual(status.packages, ("linux-firmware",))

    def test_missing_package_marks_found_device(self):
        with tempfile.TemporaryDirectory() as root:
            report = self.evaluate(root, [hardware.Item("bluetooth", "hci0", "Bluetooth adaptér")],
                                   base=fake_base(["mesa-dri-drivers", "pipewire"]))
        status = report.statuses[0]
        self.assertEqual(status.state, "package")
        self.assertEqual(status.packages, ("bluez",))

    def test_saved_connections_are_not_devices(self):
        with tempfile.TemporaryDirectory() as root:
            report = self.evaluate(root, [hardware.Item("connection", "Domáca", "Domáca"),
                                          hardware.Item("vpn", "Práca", "Práca")])
        self.assertEqual(report.statuses, [])

    def test_unreadable_kernel_log_does_not_claim_success(self):
        def run(argv):
            raise OSError("%s: zakázané" % argv[0])
        with tempfile.TemporaryDirectory() as root:
            inv = hardware.Inventory(items=[hardware.Item("computer", "cpu", "Procesor")])
            report = hwstatus.evaluate(inv, root=root, base=fake_base(["mesa-dri-drivers", "pipewire", "bluez"]),
                                       log=None, run=run)
        self.assertEqual(report.statuses[0].state, "unknown")
        self.assertTrue(any("Záznam jadra" in p for p in report.problems))

    def test_faults_are_sorted_by_urgency(self):
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:01:00.0", vendor="10de", cls="030000")
            pci_device(root, "0000:02:00.0", cls="0c0330")
            report = self.evaluate(root, [hardware.Item("platform", "0000:02:00.0", "USB radič"),
                                          hardware.Item("graphics", "0000:01:00.0", "NVIDIA")])
        self.assertEqual([s.state for s in report.faults], ["repo", "unsupported"])

    def test_for_item_finds_status(self):
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:01:00.0", driver="amdgpu")
            report = self.evaluate(root, [hardware.Item("graphics", "0000:01:00.0", "AMD")])
        self.assertIsNotNone(report.for_item("graphics", "0000:01:00.0"))
        self.assertIsNone(report.for_item("graphics", "0000:09:00.0"))


class Unclaimed(unittest.TestCase):
    """Skupina Ostatné: zariadenie, ktoré sa neprihlásilo nikde, musí dostať dôvod, nie „ok“."""

    def evaluate(self, root, items, base=None, log=""):
        return hwstatus.evaluate(hardware.Inventory(items=list(items)), root=root,
                                 base=base or fake_base(["mesa-dri-drivers", "pipewire", "bluez"]),
                                 log=log, run=no_lspci)

    def item(self, slot, cls="028000", driver=""):
        return hardware.Item("other", slot, "Intel Wi-Fi 6E", "Network controller · bez ovládača",
                             "nezaradené", {"bus": "pci", "slot": slot, "class": cls, "driver": driver})

    def test_without_driver_says_why_and_what_would_help(self):
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:04:00.0", cls="028000")
            report = self.evaluate(root, [self.item("0000:04:00.0")])
        status = report.statuses[0]
        self.assertTrue(status.unclaimed)
        self.assertNotEqual(status.state, "ok")
        self.assertIn("Bez ovládača", status.reason)

    def test_firmware_failure_is_the_reason(self):
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:04:00.0", cls="028000")
            report = self.evaluate(root, [self.item("0000:04:00.0")], log=LOG)
        status = report.statuses[0]
        self.assertEqual(status.state, "firmware")
        self.assertIn("iwlwifi-so-a0-gf-a0-83.ucode", status.reason)

    def test_nvidia_without_driver_still_points_to_the_repo(self):
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:01:00.0", vendor="10de", cls="030000")
            report = self.evaluate(root, [hardware.Item("other", "0000:01:00.0", "NVIDIA GeForce", "", "nezaradené",
                                                        {"bus": "pci", "slot": "0000:01:00.0", "class": "0300"})])
        self.assertEqual(report.statuses[0].state, "repo")
        self.assertIn("akmod-nvidia", report.statuses[0].packages)

    def test_bound_driver_without_interface_is_unknown_not_ok(self):
        with tempfile.TemporaryDirectory() as root:
            pci_device(root, "0000:04:00.0", cls="028000", driver="iwlwifi")
            report = self.evaluate(root, [self.item("0000:04:00.0", driver="iwlwifi")])
        status = report.statuses[0]
        self.assertEqual(status.state, "unknown")
        self.assertIn("nevytvorilo rozhranie", status.reason)

    def test_unnamed_usb_device_is_unknown_with_its_id(self):
        with tempfile.TemporaryDirectory() as root:
            report = self.evaluate(root, [hardware.Item("other", "usb-1-2", "Neznáme USB zariadenie",
                                                        "USB 05e3:0610 · port 1-2", "neidentifikované",
                                                        {"bus": "usb", "usb_id": "05e3:0610"})])
        status = report.statuses[0]
        self.assertEqual(status.state, "unknown")
        self.assertIn("05e3:0610", status.reason)
        self.assertTrue(status.unclaimed)


if __name__ == "__main__":
    unittest.main()
