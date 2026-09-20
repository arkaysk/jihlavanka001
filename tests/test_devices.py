import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import devices  # noqa: E402


def node(name, typ, **kw):
    base = {"name": name, "path": "/dev/" + name, "kname": name, "maj:min": "8:0", "type": typ,
            "rm": False, "ro": False, "tran": None, "size": 0, "fstype": None, "label": None,
            "uuid": None, "mountpoints": [None], "model": None, "vendor": None}
    base.update(kw)
    return base


# skutočný stav VM latteOSdev: systémový SATA disk, USB disk bez súborového systému, CD, zram
SDA = node("sda", "disk", tran="sata", size=58194853888, model="VBOX HARDDISK", vendor="ATA     ", children=[
    node("sda1", "part", fstype="vfat", uuid="083B-4020", mountpoints=["/boot/efi"], size=629145600),
    node("sda2", "part", fstype="xfs", uuid="2814130a", mountpoints=["/boot"], size=2147483648),
    node("sda3", "part", fstype="LVM2_member", uuid="33DrP1", size=55416193024, children=[
        node("fedora-root", "lvm", kname="dm-0", path="/dev/mapper/fedora-root", fstype="xfs",
             uuid="6dfa39d1", mountpoints=["/"], size=16106127360, **{"maj:min": "252:0"}),
    ]),
])
SDB = node("sdb", "disk", tran="usb", size=151261184, model="HARDDISK", vendor="VBOX    ", **{"maj:min": "8:16"})
SR0 = node("sr0", "rom", tran="ata", rm=True, ro=True, size=53215232, fstype="iso9660", label="VBox_GAs_7.2.18",
           uuid="2026-09-14-16-37-49-70", model="CD-ROM", vendor="VBOX    ", **{"maj:min": "11:0"})
ZRAM = node("zram0", "disk", fstype="swap", uuid="ded7010b", mountpoints=["[SWAP]"], size=8589934592)

VBOXSF = "294 42 0:66 / /media/sf_ProjectLatteOS rw,nodev,relatime shared:569 - vboxsf ProjectLatteOS rw,gid=987"


def detect(*nodes, mountinfo="", floppy=False, module=False):
    return devices.detect(lsblk={"blockdevices": list(nodes)}, mountinfo=mountinfo,
                          floppy_controller=floppy, floppy_module=module)


class DetectTest(unittest.TestCase):
    def by_node(self, found):
        return {d.node or d.key: d for d in found}

    def test_current_vm(self):
        found = detect(SDA, SDB, SR0, ZRAM, mountinfo=VBOXSF)
        got = [(d.kind, d.state, d.node or d.share_name) for d in found]
        self.assertEqual(got, [
            ("system", "mounted", "/dev/mapper/fedora-root"),
            ("usb", "no-fs", "/dev/sdb"),
            ("optical", "unmounted", "/dev/sr0"),
            ("share", "mounted", "ProjectLatteOS"),
        ])

    def test_system_internals_and_swap_are_not_sources(self):
        found = detect(SDA, ZRAM)
        nodes = [d.node for d in found]
        self.assertNotIn("/dev/sda1", nodes)        # /boot/efi
        self.assertNotIn("/dev/sda2", nodes)        # /boot
        self.assertNotIn("/dev/sda3", nodes)        # člen LVM
        self.assertNotIn("/dev/zram0", nodes)

    def test_usb_partitions_inherit_usb_kind(self):
        usb = node("sdc", "disk", tran="usb", rm=True, size=8_000_000_000, model="Flash", children=[
            node("sdc1", "part", fstype="vfat", uuid="AAAA-BBBB", label="FOTKY", size=7_000_000_000),
            node("sdc2", "part", fstype="ext4", uuid="cccc", mountpoints=["/run/media/user/DATA"], size=900_000_000),
        ])
        found = self.by_node(detect(usb))
        self.assertEqual(set(found), {"/dev/sdc1", "/dev/sdc2"})       # disk sám sa neukazuje
        self.assertEqual(found["/dev/sdc1"].kind, "usb")
        self.assertEqual(found["/dev/sdc1"].state, "unmounted")
        self.assertTrue(found["/dev/sdc1"].mountable)
        self.assertEqual(found["/dev/sdc1"].label, "FOTKY")
        self.assertEqual(found["/dev/sdc2"].state, "mounted")
        self.assertEqual(found["/dev/sdc2"].mountpoint, "/run/media/user/DATA")
        self.assertTrue(all(d.removable for d in found.values()))

    def test_extra_sata_disk_without_filesystem(self):
        extra = node("sdd", "disk", tran="sata", size=10 * 10**9, model="VBOX HARDDISK", **{"maj:min": "8:48"})
        found = detect(SDA, extra)
        disk = [d for d in found if d.node == "/dev/sdd"][0]
        self.assertEqual((disk.kind, disk.state, disk.removable), ("disk", "no-fs", False))

    def test_formatted_internal_disk_is_listed_unmounted(self):
        data = node("sdd", "disk", tran="sata", children=[node("sdd1", "part", fstype="ext4", uuid="d1", size=5 * 10**9)])
        found = [d for d in detect(SDA, data) if d.node == "/dev/sdd1"][0]
        self.assertEqual((found.kind, found.state, found.removable), ("disk", "unmounted", False))

    def test_optical_without_media(self):
        empty = node("sr0", "rom", tran="ata", rm=True, size=0, **{"maj:min": "11:0"})
        found = detect(empty)[0]
        self.assertEqual((found.kind, found.state), ("optical", "no-media"))
        self.assertEqual(found.state_text, "bez média")

    def test_floppy_drive_with_driver(self):
        fd = node("fd0", "disk", rm=True, size=0, **{"maj:min": "2:0"})
        found = detect(fd, floppy=True)          # driver vidí zariadenie: ACPI sa nepoužije
        self.assertEqual([(d.kind, d.state) for d in found], [("floppy", "no-media")])
        fd = node("fd0", "disk", rm=True, size=1474560, fstype="vfat", uuid="F1F1-0001", **{"maj:min": "2:0"})
        self.assertEqual([(d.kind, d.state) for d in detect(fd)], [("floppy", "unmounted")])

    def test_floppy_controller_without_driver(self):
        found = detect(SDA, floppy=True, module=False)
        floppy = [d for d in found if d.kind == "floppy"]
        self.assertEqual(len(floppy), 1)
        self.assertEqual(floppy[0].state, "no-driver")
        self.assertFalse(floppy[0].mountable)
        self.assertIn("modprobe floppy", devices.STATE_HELP["no-driver"])

    def test_floppy_controller_with_driver_but_no_drive(self):
        floppy = [d for d in detect(SDA, floppy=True, module=True) if d.kind == "floppy"]
        self.assertEqual([d.state for d in floppy], ["no-drive"])
        self.assertFalse(floppy[0].mountable)
        self.assertEqual(floppy[0].state_text, "bez mechaniky")

    def test_no_floppy_when_firmware_says_absent(self):
        self.assertEqual([d for d in detect(SDA, floppy=False) if d.kind == "floppy"], [])

    def test_encrypted_volume_is_listed_locked(self):
        luks = node("sde1", "part", fstype="crypto_LUKS", uuid="l1", size=10**9)
        found = detect(luks)[0]
        self.assertEqual(found.state, "locked")
        self.assertFalse(found.mountable)

    def test_loop_devices_are_ignored(self):
        self.assertEqual(detect(node("loop0", "loop", fstype="squashfs", mountpoints=["/var/lib/snap/x"])), [])


class SharesTest(unittest.TestCase):
    def test_virtualbox_share(self):
        shares = devices.parse_shares(VBOXSF)
        self.assertEqual(len(shares), 1)
        self.assertEqual((shares[0].kind, shares[0].share_name, shares[0].mountpoint),
                         ("share", "ProjectLatteOS", "/media/sf_ProjectLatteOS"))
        self.assertEqual(shares[0].key, "share:vboxsf:ProjectLatteOS")

    def test_network_shares_and_escaped_names(self):
        text = "\n".join([
            "1 0 0:1 / /mnt/nas\\040data rw - cifs //nas.local/Foto\\040archiv rw",
            "2 0 0:2 / /mnt/nfs rw - nfs4 server:/export/media rw",
            "3 0 8:1 / / rw - xfs /dev/sda1 rw",
            "4 0 0:3 / /proc rw - proc proc rw",
        ])
        shares = devices.parse_shares(text)
        self.assertEqual([(s.share_name, s.mountpoint) for s in shares],
                         [("Foto archiv", "/mnt/nas data"), ("media", "/mnt/nfs")])

    def test_duplicate_mounts_and_garbage_lines(self):
        line = "294 42 0:66 / /media/sf_X rw - vboxsf X rw"
        self.assertEqual(len(devices.parse_shares(line + "\n" + line + "\nnezmysel\n\n")), 1)


if __name__ == "__main__":
    unittest.main()
