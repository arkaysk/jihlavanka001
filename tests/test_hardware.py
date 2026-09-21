import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import hardware, outputs  # noqa: E402

LSPCI = '''00:00.0 "Host bridge [0600]" "Intel Corporation [8086]" "440FX - 82441FX PMC [Natoma] [1237]" -r02 -p00 "" ""
00:02.0 "VGA compatible controller [0300]" "VMware [15ad]" "SVGA II Adapter [0405]" -p00 "VMware [15ad]" "SVGA II Adapter [0405]"
00:03.0 "Ethernet controller [0200]" "Intel Corporation [8086]" "82540EM Gigabit Ethernet Controller [100e]" -r02 -p00 "" ""
00:05.0 "Multimedia audio controller [0401]" "Intel Corporation [8086]" "82801AA AC'97 Audio Controller [2415]" -r01 -p00 "" ""
00:0d.0 "SATA controller [0106]" "Intel Corporation [8086]" "82801HM/HEM SATA Controller [AHCI mode] [2829]" -r02 -p01 "" ""
'''
LSBLK = json.dumps({"blockdevices": [
    {"name": "sda", "type": "disk", "size": "54,2G", "model": "SSD 860", "vendor": "Samsung", "tran": "sata", "rota": False},
    {"name": "sdb", "type": "disk", "size": "14,9G", "model": "Flash", "vendor": "USB", "tran": "usb", "rota": True},
    {"name": "sr0", "type": "rom", "size": "1024M", "model": "DVD", "vendor": "HL", "tran": "sata", "rota": True},
    {"name": "loop0", "type": "loop", "size": "50M", "model": None, "vendor": None, "tran": None, "rota": True},
    {"name": "zram0", "type": "disk", "size": "4G", "model": None, "vendor": None, "tran": None, "rota": False},
]})
INPUT = '''I: Bus=0019 Vendor=0000 Product=0001 Version=0000
N: Name="Power Button"
H: Handlers=kbd event0
B: PROP=0
B: EV=3

I: Bus=0011 Vendor=0001 Product=0001 Version=ab41
N: Name="AT Translated Set 2 keyboard"
H: Handlers=sysrq kbd leds event2
B: PROP=0
B: EV=120013

I: Bus=0003 Vendor=046d Product=c52b Version=0111
N: Name="Logitech USB Receiver Mouse"
H: Handlers=mouse0 event3
B: PROP=0
B: EV=17

I: Bus=0018 Vendor=06cb Product=cd41 Version=0100
N: Name="SYNA8004:00 06CB:CD41 Touchpad"
H: Handlers=mouse1 event4
B: PROP=5
B: EV=b

I: Bus=0019 Vendor=0000 Product=0005 Version=0000
N: Name="Video Bus"
H: Handlers=kbd event5
B: PROP=0
B: EV=3
'''
ASOUND = ''' 0 [PCH            ]: HDA-Intel - HDA Intel PCH
                      HDA Intel PCH at 0xf7210000 irq 130
'''


def put(root, path, text=""):
    full = os.path.join(root, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(text)


NMCLI = """Drôtové pripojenie 1:802-3-ethernet:enp0s3:activated
Doma\\: 5G:802-11-wireless::
Firma VPN:vpn::
wg0:wireguard:wg0:activated
lo:loopback:lo:activated
docker0:bridge:docker0:activated
"""


def fake_run(argv):
    if argv[0] == "lspci":
        return LSPCI
    if argv[0] == "lsblk":
        return LSBLK
    if argv[0] == "nmcli":
        return NMCLI
    raise OSError("neznámy príkaz")


class InventoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        r = cls.root = cls._tmp.name
        put(r, "proc/asound/cards", ASOUND)
        put(r, "proc/bus/input/devices", INPUT)
        put(r, "proc/cpuinfo", "processor : 0\nmodel name : Test CPU @ 3GHz\nprocessor : 1\nmodel name : Test CPU @ 3GHz\n")
        put(r, "proc/meminfo", "MemTotal:       16777216 kB\n")
        put(r, "sys/class/dmi/id/sys_vendor", "ACME\n")
        put(r, "sys/class/dmi/id/product_name", "Laptop 1\n")
        put(r, "sys/class/dmi/id/bios_version", "1.2.3\n")
        # sieť: fyzická karta, Wi-Fi a virtuálny most
        put(r, "sys/devices/pci0000:00/0000:00:03.0/net/enp0s3/operstate", "up\n")
        os.makedirs(os.path.join(r, "sys/class/net"), exist_ok=True)
        os.symlink("../../devices/pci0000:00/0000:00:03.0/net/enp0s3", os.path.join(r, "sys/class/net/enp0s3"))
        os.symlink("../../../0000:00:03.0", os.path.join(r, "sys/devices/pci0000:00/0000:00:03.0/net/enp0s3/device"))
        put(r, "sys/devices/pci0000:00/0000:00:19.0/net/wlp3s0/operstate", "down\n")
        os.makedirs(os.path.join(r, "sys/devices/pci0000:00/0000:00:19.0/net/wlp3s0/wireless"))
        os.symlink("../../devices/pci0000:00/0000:00:19.0/net/wlp3s0", os.path.join(r, "sys/class/net/wlp3s0"))
        put(r, "sys/devices/virtual/net/virbr0/operstate", "up\n")
        os.symlink("../../devices/virtual/net/virbr0", os.path.join(r, "sys/class/net/virbr0"))
        put(r, "sys/devices/virtual/net/lo/operstate", "unknown\n")
        os.symlink("../../devices/virtual/net/lo", os.path.join(r, "sys/class/net/lo"))
        # USB: myš (HID, patrí do vstupu), tlačiareň (ostáva v USB), koreňový rozbočovač
        put(r, "sys/bus/usb/devices/1-1/product", "USB Receiver\n")
        put(r, "sys/bus/usb/devices/1-1/bDeviceClass", "00\n")
        put(r, "sys/bus/usb/devices/1-1/1-1:1.0/bInterfaceClass", "03\n")
        put(r, "sys/bus/usb/devices/1-2/product", "LaserJet 100\n")
        put(r, "sys/bus/usb/devices/1-2/manufacturer", "HP\n")
        put(r, "sys/bus/usb/devices/1-2/bDeviceClass", "00\n")
        put(r, "sys/bus/usb/devices/1-2/1-2:1.0/bInterfaceClass", "07\n")
        put(r, "sys/bus/usb/devices/usb1/product", "xHCI Host Controller\n")
        put(r, "sys/bus/usb/devices/usb1/bDeviceClass", "09\n")
        put(r, "sys/class/power_supply/BAT0/type", "Battery\n")
        put(r, "sys/class/power_supply/BAT0/capacity", "87\n")
        put(r, "sys/class/power_supply/BAT0/status", "Discharging\n")
        put(r, "sys/class/power_supply/AC/type", "Mains\n")
        put(r, "sys/class/power_supply/AC/online", "0\n")
        put(r, "sys/class/video4linux/video0/name", "Integrated Camera\n")
        put(r, "sys/class/video4linux/video0/index", "0\n")
        put(r, "sys/class/video4linux/video1/name", "Integrated Camera\n")
        put(r, "sys/class/video4linux/video1/index", "1\n")
        put(r, "sys/class/drm/card0-eDP-1/status", "connected\n")
        cls.monitor = outputs.Head(5, name="eDP-1", make="BOE", model="0868", width_mm=310, height_mm=174)
        cls.monitor.modes[6] = outputs.Mode(6, 1920, 1080, 60000, True)
        cls.monitor.current_mode = 6
        cls.inv = hardware.scan(root=r, heads=[cls.monitor], run=fake_run)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def names(self, gid):
        return [i.name for i in self.inv.group(gid)]

    def test_groups_come_in_a_fixed_order_and_only_when_not_empty(self):
        ids = [gid for gid, _t, _i in self.inv.groups()]
        self.assertEqual(ids, [g for g in hardware.GROUPS if g in ids])
        self.assertNotIn("bluetooth", ids)              # žiadny adaptér, tak žiadna prázdna skupina

    def test_every_device_is_in_exactly_one_group(self):
        seen = set()
        for item in self.inv.items:
            self.assertNotIn((item.group, item.key), seen)
            seen.add((item.group, item.key))
        self.assertEqual(len(self.names("input")), 3)

    def test_display_comes_from_the_compositor_with_its_connector(self):
        item = self.inv.group("display")[0]
        self.assertEqual(item.name, "BOE 0868")
        self.assertIn("1920 × 1080", item.detail)
        self.assertEqual(item.settings_uri, "settings://hardware/display/eDP-1")

    def test_pci_devices_with_their_own_group_are_not_repeated_in_platform(self):
        self.assertEqual(self.names("graphics"), ["VMware SVGA II Adapter"])
        platform = " ".join(self.names("platform"))
        self.assertIn("440FX", platform)
        self.assertIn("SATA", platform)
        self.assertNotIn("Ethernet", platform)
        self.assertNotIn("AC'97", platform)

    def test_network_lists_physical_adapters_only_and_names_them_from_pci(self):
        self.assertEqual(self.names("network"), ["Intel 82540EM Gigabit Ethernet Controller", "wlp3s0"])
        kinds = {i.key: i.extra["wireless"] for i in self.inv.group("network")}
        self.assertEqual(kinds, {"enp0s3": False, "wlp3s0": True})
        self.assertEqual(self.inv.group("network")[0].status, "pripojené")

    def test_input_skips_system_buttons_and_classifies(self):
        by_name = {i.name: i.detail for i in self.inv.group("input")}
        self.assertEqual(by_name, {"AT Translated Set 2 keyboard": "Klávesnica", "Logitech USB Receiver Mouse": "Myš",
                                   "SYNA8004:00 06CB:CD41 Touchpad": "Touchpad"})

    def test_usb_keeps_only_what_has_no_group_of_its_own(self):
        self.assertEqual(self.names("usb"), ["LaserJet 100"])

    def test_disks_are_whole_devices_and_optical_drives_are_a_group_of_their_own(self):
        self.assertEqual(self.names("storage"), ["Samsung SSD 860", "USB Flash"])
        self.assertEqual(self.names("optical"), ["HL DVD"])
        details = [i.detail for i in self.inv.group("storage")]
        self.assertIn("SSD", details[0])
        self.assertIn("USB disk", details[1])
        self.assertIn("Optická mechanika", self.inv.group("optical")[0].detail)

    def test_no_file_system_content_is_listed(self):
        # správca zariadení ukazuje zariadenia, nie zväzky ani ich obsah (zdieľané priečinky, oddiely)
        for item in self.inv.items:
            self.assertNotIn("share", item.group)
            self.assertNotIn("vboxsf", item.detail)
        self.assertNotIn("sda1", " ".join(i.key for i in self.inv.group("storage")))

    def test_power_camera_audio_and_computer(self):
        self.assertEqual([(i.name, i.status) for i in self.inv.group("power")],
                         [("Batéria", "Discharging"), ("Sieťové napájanie", "nepripojené")])
        self.assertEqual(self.names("camera"), ["Integrated Camera"])          # druhý uzol tej istej kamery sa neráta
        self.assertEqual(self.names("audio"), ["HDA Intel PCH"])
        computer = {i.key: i for i in self.inv.group("computer")}
        self.assertEqual(computer["dmi"].name, "ACME Laptop 1")
        self.assertEqual(computer["cpu"].detail, "2 jadier (vlákien)")
        self.assertEqual(computer["memory"].detail, "16,0 GB")

    def test_connections_and_vpn_come_from_networkmanager(self):
        connections = {i.name: (i.status, i.detail) for i in self.inv.group("connection")}
        self.assertEqual(connections, {"Drôtové pripojenie 1": ("pripojené", "Kábel · enp0s3"),
                                       "Doma: 5G": ("nepripojené", "Wi-Fi")})           # \\: v názve je dvojbodka
        vpn = {i.name: i.status for i in self.inv.group("vpn")}
        self.assertEqual(vpn, {"Firma VPN": "nepripojené", "wg0": "pripojené"})
        names = " ".join(i.name for i in self.inv.group("connection") + self.inv.group("vpn"))
        self.assertNotIn("docker0", names)                                                # virtuálne siete nie sú pripojenia
        self.assertNotIn("lo ", names + " ")

    def test_tabs_devices_and_networks(self):
        devices = [gid for gid, _t, _i in self.inv.groups("devices")]
        networks = [gid for gid, _t, _i in self.inv.groups("networks")]
        self.assertEqual(networks, ["network", "connection", "vpn"])
        self.assertIn("network", devices)                                    # sieťové karty sú na oboch záložkách
        self.assertNotIn("vpn", devices)
        self.assertNotIn("connection", devices)
        self.assertLess(devices.index("graphics"), devices.index("optical"))
        self.assertEqual(devices[:4], ["display", "graphics", "audio", "network"])

    def test_empty_groups_are_shown_only_where_they_explain_something(self):
        with tempfile.TemporaryDirectory() as root:
            inv = hardware.scan(root=root, heads=[], run=lambda argv: {"lspci": "", "lsblk": '{"blockdevices": []}',
                                                                       "nmcli": ""}[argv[0]])
        self.assertEqual([gid for gid, _t, _i in inv.groups("networks")], ["connection", "vpn"])
        self.assertIn("VPN", hardware.SHOW_EMPTY["vpn"])
        self.assertEqual([gid for gid, _t, _i in inv.groups("devices")], [])          # prázdne zariadenia sa neukazujú

    def test_every_device_has_an_icon_by_kind(self):
        icons = {(i.group, i.name): i.icons[0] for i in self.inv.items}
        self.assertEqual(icons[("input", "AT Translated Set 2 keyboard")], "input-keyboard-symbolic")
        self.assertEqual(icons[("input", "Logitech USB Receiver Mouse")], "input-mouse-symbolic")
        self.assertEqual(icons[("input", "SYNA8004:00 06CB:CD41 Touchpad")], "input-touchpad-symbolic")
        self.assertEqual(icons[("storage", "Samsung SSD 860")], "drive-harddisk-solidstate-symbolic")
        self.assertEqual(icons[("storage", "USB Flash")], "drive-removable-media-symbolic")
        self.assertEqual(icons[("optical", "HL DVD")], "media-optical-symbolic")
        self.assertEqual(icons[("graphics", "VMware SVGA II Adapter")], "latte-gpu-symbolic")
        self.assertEqual(icons[("network", "wlp3s0")], "network-wireless-symbolic")
        self.assertEqual(icons[("computer", "Test CPU @ 3GHz")], "latte-cpu-symbolic")
        for item in self.inv.items:
            self.assertTrue(item.icons[-1] == "computer-symbolic")                    # vždy je čo nakresliť

    def test_custom_icons_exist(self):
        from latte_common import paths
        used = {n for icons in hardware.GROUP_ICONS.values() for n in icons if n.startswith("latte-")}
        used |= {"latte-cpu-symbolic", "latte-memory-symbolic"}
        for name in used:
            self.assertTrue(os.path.isfile(os.path.join(paths.data_dir(), "icons", name + ".svg")), name)

    def test_settings_target_by_group(self):
        uris = {i.group: i.settings_uri for i in self.inv.items}
        self.assertEqual(uris["audio"], "settings://hardware/sound")
        self.assertEqual(uris["network"], "settings://hardware/network")
        self.assertEqual(uris["storage"], "settings://hardware/drives")
        self.assertEqual(uris["computer"], "settings://system/about")

    def test_settings_targets_exist_in_the_settings_tree(self):
        from latte_common import settings
        registry = settings.Registry()
        for gid, (_title, target) in hardware.GROUPS.items():
            group, page = target.split("/")
            self.assertEqual(registry.resolve(target)[0], "page", "%s -> %s" % (gid, target))
            self.assertEqual(registry.resolve(target)[1].group, group)


class NmcliParsingTest(unittest.TestCase):
    def test_escaped_colon_and_backslash(self):
        self.assertEqual(hardware.split_nmcli("a\\:b:vpn:dev:activated"), ["a:b", "vpn", "dev", "activated"])
        self.assertEqual(hardware.split_nmcli("x\\\\y:z"), ["x\\y", "z"])
        self.assertEqual(hardware.split_nmcli("a::"), ["a", "", ""])

    def test_short_or_broken_lines_are_skipped(self):
        self.assertEqual(hardware.read_connections("\njen-nazov\n:802-3-ethernet:eth0:activated\n"), [])


class FailureTest(unittest.TestCase):
    def test_missing_tools_and_compositor_are_reported_not_hidden(self):
        def broken(argv):
            raise OSError("%s nie je nainštalovaný" % argv[0])

        with tempfile.TemporaryDirectory() as root:
            put(root, "sys/class/drm/card0-HDMI-A-1/status", "connected\n")
            old = os.environ.pop("WAYLAND_DISPLAY", None)
            try:
                inv = hardware.scan(root=root, run=broken)
            finally:
                if old is not None:
                    os.environ["WAYLAND_DISPLAY"] = old
        text = " | ".join(inv.problems)
        self.assertIn("lspci", text)
        self.assertIn("lsblk", text)
        self.assertIn("nmcli", text)
        self.assertIn("Monitory", text)
        # monitor sa aspoň ukáže z DRM, s poznámkou, že údaje od kompozitora nie sú
        display = inv.group("display")[0]
        self.assertEqual(display.extra["connector"], "HDMI-A-1")
        self.assertIn("bez údajov od kompozitora", display.detail)

    def test_input_classification_edge_cases(self):
        self.assertIsNone(hardware.classify_input({"name": "Lid Switch", "handlers": ["event1"], "ev": 21, "prop": 0}))
        self.assertEqual(hardware.classify_input({"name": "Wacom Tablet", "handlers": ["mouse2"], "ev": 0, "prop": 0}), "Tablet")
        self.assertEqual(hardware.classify_input({"name": "Xbox Controller", "handlers": ["js0"], "ev": 0, "prop": 0}), "Ovládač hier")
        self.assertIsNone(hardware.classify_input({"name": "Mystery", "handlers": ["event9"], "ev": 3, "prop": 0}))




class OtherGroup(unittest.TestCase):
    """Zásada 6: zo zoznamu zariadení nesmie nič vypadnúť. Sieťová karta bez ovládača nevytvorí
    rozhranie v /sys/class/net, zvuková kartu v /proc/asound — takže by zmizli. Skupina Ostatné
    zariadenia ich podrží aj s dôvodom."""

    LSPCI = ('00:02.0 "VGA compatible controller [0300]" "Intel Corporation [8086]" "UHD [9a49]" -p00 "" ""\n'
             '04:00.0 "Network controller [0280]" "Intel Corporation [8086]" "Wi-Fi 6E [2725]" -p00 "" ""\n'
             '00:1f.3 "Audio device [0403]" "Intel Corporation [8086]" "Smart Sound [a0c8]" -p00 "" ""\n'
             '00:00.0 "Host bridge [0600]" "Intel Corporation [8086]" "Host [9a14]" -p00 "" ""\n')

    def machine(self, root, with_wifi_driver=False):
        """Falošný stroj: grafika a zvuk fungujú, Wi-Fi je na zbernici, ale bez rozhrania."""
        for slot, cls, driver in (("0000:00:02.0", "030000", "i915"),
                                  ("0000:00:1f.3", "040300", "snd_hda_intel"),
                                  ("0000:04:00.0", "028000", "iwlwifi" if with_wifi_driver else None),
                                  ("0000:00:00.0", "060000", None)):
            base = os.path.join(root, "sys/bus/pci/devices", slot)
            os.makedirs(base, exist_ok=True)
            with open(os.path.join(base, "class"), "w", encoding="utf-8") as f:
                f.write("0x%s\n" % cls)
            if driver:
                target = os.path.join(root, "sys/bus/pci/drivers", driver)
                os.makedirs(target, exist_ok=True)
                os.symlink(target, os.path.join(base, "driver"))
        # Zvuková karta sa prihlásila, Wi-Fi nie.
        os.makedirs(os.path.join(root, "proc/asound"), exist_ok=True)
        with open(os.path.join(root, "proc/asound/cards"), "w", encoding="utf-8") as f:
            f.write(" 0 [PCH            ]: HDA-Intel - HDA Intel PCH\n                      HDA Intel PCH at 0xa000\n")
        card = os.path.join(root, "sys/class/sound/card0")
        os.makedirs(card, exist_ok=True)
        os.symlink(os.path.join(root, "sys/bus/pci/devices/0000:00:1f.3"), os.path.join(card, "device"))

    def scan(self, root):
        def run(argv):
            if argv[0] == "lspci":
                return self.LSPCI
            raise OSError("%s: v skúške nie je" % argv[0])
        return hardware.scan(root=root, heads=[], run=run)

    def test_card_without_driver_does_not_disappear(self):
        with tempfile.TemporaryDirectory() as root:
            self.machine(root)
            inv = self.scan(root)
        others = inv.group("other")
        self.assertEqual([i.key for i in others], ["0000:04:00.0"])
        self.assertEqual(others[0].name, "Intel Wi-Fi 6E")
        self.assertIn("bez ovládača", others[0].detail)
        self.assertEqual(others[0].status, "nezaradené")
        self.assertEqual(others[0].extra["class"], "0280")

    def test_claimed_devices_are_not_repeated(self):
        with tempfile.TemporaryDirectory() as root:
            self.machine(root)
            inv = self.scan(root)
        keys = [i.key for i in inv.group("other")]
        self.assertNotIn("0000:00:1f.3", keys)              # zvuk sa prihlásil ako karta
        self.assertNotIn("0000:00:02.0", keys)              # grafika má vlastnú skupinu
        self.assertNotIn("0000:00:00.0", keys)              # most je medzi Čipsetom a radičmi

    def test_audio_item_remembers_its_slot(self):
        with tempfile.TemporaryDirectory() as root:
            self.machine(root)
            inv = self.scan(root)
        self.assertEqual(inv.group("audio")[0].extra["slot"], "0000:00:1f.3")

    def test_group_is_in_tab_and_has_an_icon(self):
        self.assertIn("other", hardware.TAB_GROUPS["devices"])
        self.assertIn("other", hardware.GROUP_ICONS)
        self.assertEqual(hardware.Item("other", "x", "X").settings_uri, "settings://hardware/hwdiag")

    def test_usb_device_without_a_name_lands_in_other(self):
        with tempfile.TemporaryDirectory() as root:
            device = os.path.join(root, "sys/bus/usb/devices/1-2")
            os.makedirs(device)
            for name, value in (("idVendor", "05e3"), ("idProduct", "0610"), ("bDeviceClass", "ff")):
                with open(os.path.join(device, name), "w", encoding="utf-8") as f:
                    f.write(value + "\n")
            items = hardware.read_usb(root)
        self.assertEqual([i.group for i in items], ["other"])
        self.assertIn("05e3:0610", items[0].detail)
        self.assertEqual(items[0].extra["bus"], "usb")

    def test_named_usb_device_stays_in_its_group(self):
        with tempfile.TemporaryDirectory() as root:
            device = os.path.join(root, "sys/bus/usb/devices/1-3")
            os.makedirs(device)
            for name, value in (("product", "Tlačiareň"), ("bDeviceClass", "00")):
                with open(os.path.join(device, name), "w", encoding="utf-8") as f:
                    f.write(value + "\n")
            items = hardware.read_usb(root)
        self.assertEqual([i.group for i in items], ["usb"])


if __name__ == "__main__":
    unittest.main()
