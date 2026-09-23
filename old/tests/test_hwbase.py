import os
import sys
import tempfile
import tomllib
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import hwbase, paths  # noqa: E402

PLAN_TOML = """
[base]
id = "latteos-base"
title = "Základ"

[repo.rpmfusion-nonfree]
title = "RPM Fusion Nonfree"
release = "rpmfusion-nonfree-release"
url = "https://example.invalid/nonfree-$releasever.noarch.rpm"
note = "Proprietárne."

[[group]]
id = "graphics"
title = "Grafika"
why = "3D."
devices = ["graphics"]
required = ["mesa-dri-drivers"]
optional = ["mesa-dri-drivers.i686"]
[[group.extra]]
repo = "rpmfusion-nonfree"
packages = ["akmod-nvidia"]
note = "Len s kartou NVIDIA."

[[group]]
id = "audio"
title = "Zvuk"
devices = ["audio"]
required = ["pipewire", "alsa-ucm"]
"""

# Ako odpovedá `rpm -q --qf`: nainštalované vo formáte, chýbajúce preloženou hláškou bez oddeľovača.
def fake_rpm(installed):
    def run(argv):
        out = []
        for name in argv[argv.index("%{NAME}" + hwbase.MARK + "%{VERSION}-%{RELEASE}" + hwbase.MARK + "%{ARCH}\n") + 1:]:
            builds = installed.get(name)
            if builds:
                out += [hwbase.MARK.join((name, version, arch)) for version, arch in builds]
            else:
                out.append("balík %s nie je nainštalovaný" % name)
        return "\n".join(out) + "\n"
    return run


def plan():
    return hwbase.parse(tomllib.loads(PLAN_TOML), "skúška")


class ParsePlan(unittest.TestCase):
    def test_groups_and_packages(self):
        p = plan()
        self.assertEqual([g.id for g in p.groups], ["graphics", "audio"])
        names = [x.name for x in p.groups[0].packages]
        self.assertEqual(names, ["mesa-dri-drivers", "mesa-dri-drivers.i686", "akmod-nvidia"])
        self.assertEqual([x.name for x in p.groups[0].required()], ["mesa-dri-drivers"])

    def test_extra_carries_repo_and_note(self):
        extra = plan().groups[0].packages[-1]
        self.assertEqual(extra.repo, "rpmfusion-nonfree")
        self.assertFalse(extra.required)
        self.assertIn("NVIDIA", extra.note)

    def test_arch_suffix(self):
        self.assertEqual(plan().groups[0].packages[1].arch, "i686")
        self.assertEqual(plan().groups[0].packages[0].arch, "")

    def test_for_device_group(self):
        self.assertEqual([g.id for g in plan().for_device_group("audio")], ["audio"])
        self.assertEqual(plan().for_device_group("camera"), [])

    def test_unknown_repo_is_error(self):
        data = tomllib.loads(PLAN_TOML.replace('repo = "rpmfusion-nonfree"', 'repo = "vymyslene"'))
        with self.assertRaises(hwbase.BaseError):
            hwbase.parse(data, "skúška")

    def test_group_without_id_is_error(self):
        with self.assertRaises(hwbase.BaseError):
            hwbase.parse({"group": [{"title": "Bez id", "required": ["x"]}]}, "skúška")

    def test_empty_list_is_error(self):
        with self.assertRaises(hwbase.BaseError):
            hwbase.parse({}, "skúška")


class RepoFiles(unittest.TestCase):
    def test_enabled_by_default(self):
        repos = hwbase.parse_repo_file("[fedora]\nname=Fedora\n")
        self.assertEqual(repos, {"fedora": True})

    def test_enabled_key_wins(self):
        text = "[a]\nenabled=1\n\n[b]\nenabled = 0\n\n[c]\nenabled=true\n"
        self.assertEqual(hwbase.parse_repo_file(text), {"a": True, "b": False, "c": True})

    def test_enabled_repos_reads_directory(self):
        with tempfile.TemporaryDirectory() as root:
            directory = os.path.join(root, "etc", "yum.repos.d")
            os.makedirs(directory)
            with open(os.path.join(directory, "fusion.repo"), "w", encoding="utf-8") as f:
                f.write("[rpmfusion-free]\nenabled=1\n\n[rpmfusion-nonfree]\nenabled=0\n")
            with open(os.path.join(directory, "poznamka.txt"), "w", encoding="utf-8") as f:
                f.write("[nie-repo]\n")
            self.assertEqual(hwbase.enabled_repos(root), {"rpmfusion-free"})

    def test_missing_directory_is_empty(self):
        self.assertEqual(hwbase.enabled_repos("/neexistuje-latteos"), set())


class RpmQuery(unittest.TestCase):
    def test_parses_only_formatted_lines(self):
        run = fake_rpm({"pipewire": [("1.6.8", "x86_64")]})
        found = hwbase.rpm_query(["pipewire", "alsa-ucm"], run)
        self.assertEqual(found, {"pipewire": [("1.6.8", "x86_64")]})

    def test_empty_names_skips_rpm(self):
        def run(_argv):
            raise AssertionError("rpm sa nemá spúšťať")
        self.assertEqual(hwbase.rpm_query([], run), {})


class Check(unittest.TestCase):
    def check(self, installed, repos=("fedora",)):
        with tempfile.TemporaryDirectory() as root:
            directory = os.path.join(root, "etc", "yum.repos.d")
            os.makedirs(directory)
            with open(os.path.join(directory, "x.repo"), "w", encoding="utf-8") as f:
                f.write("".join("[%s]\nenabled=1\n\n" % r for r in repos))
            return hwbase.check(plan(), root=root, run=fake_rpm(installed))

    def test_states(self):
        report = self.check({"mesa-dri-drivers": [("26.2", "x86_64")], "pipewire": [("1.6", "x86_64")]})
        self.assertEqual(report.state("mesa-dri-drivers"), "installed")
        self.assertEqual(report.state("alsa-ucm"), "missing")
        self.assertEqual(report.state("akmod-nvidia"), "repo")      # repozitár nie je zapnutý

    def test_repo_enabled_makes_package_only_missing(self):
        report = self.check({"pipewire": [("1.6", "x86_64")]}, repos=("fedora", "rpmfusion-nonfree"))
        self.assertEqual(report.state("akmod-nvidia"), "missing")
        self.assertEqual(report.problems, [])

    def test_disabled_repo_is_a_fact_not_a_problem(self):
        """Vypnutý RPM Fusion nie je porucha. Na stroji s Radeonom sa nemá vôbec ozvať."""
        report = self.check({"pipewire": [("1.6", "x86_64")]})
        self.assertFalse(report.repo_enabled("rpmfusion-nonfree"))
        self.assertEqual(report.problems, [])

    def test_repo_knows_what_it_brings_and_how_to_turn_it_on(self):
        report = self.check({})
        self.assertEqual(report.repo_brings("rpmfusion-nonfree"), ("akmod-nvidia",))
        repo = report.plan.repos["rpmfusion-nonfree"]
        self.assertIn("nonfree-$releasever.noarch.rpm", repo.enable_command())

    def test_install_commands_offer_to_enable_a_disabled_repo_first(self):
        commands = self.check({}).install_commands()
        where = commands.index("dnf install akmod-nvidia")
        self.assertIn("nonfree-$releasever.noarch.rpm", commands[where - 1])

    def test_enabled_repo_needs_no_enable_command(self):
        commands = self.check({}, repos=("fedora", "rpmfusion-nonfree")).install_commands()
        self.assertFalse(any("noarch.rpm" in c for c in commands))

    def test_arch_must_match(self):
        report = self.check({"mesa-dri-drivers": [("26.2", "x86_64")]})
        self.assertEqual(report.state("mesa-dri-drivers"), "installed")
        self.assertEqual(report.state("mesa-dri-drivers.i686"), "missing")
        report = self.check({"mesa-dri-drivers": [("26.2", "x86_64"), ("26.2", "i686")]})
        self.assertEqual(report.state("mesa-dri-drivers.i686"), "installed")

    def test_complete_ignores_optional(self):
        self.assertFalse(self.check({"mesa-dri-drivers": [("1", "x86_64")]}).complete)
        report = self.check({"mesa-dri-drivers": [("1", "x86_64")], "pipewire": [("1", "x86_64")],
                             "alsa-ucm": [("1", "noarch")]})
        self.assertTrue(report.complete)
        self.assertIn("úplný", report.summary())

    def test_rpm_failure_is_a_problem_not_a_lie(self):
        def run(_argv):
            raise OSError("rpm: nenašiel sa")
        with tempfile.TemporaryDirectory() as root:
            report = hwbase.check(plan(), root=root, run=run)
        self.assertEqual(report.states, {})
        self.assertEqual(report.state("pipewire"), "unknown")
        self.assertTrue(any("rpm" in p for p in report.problems))

    def test_install_commands_separate_required_optional_and_repo(self):
        commands = self.check({"pipewire": [("1", "x86_64")]}).install_commands()
        self.assertIn("dnf install alsa-ucm mesa-dri-drivers", commands)
        self.assertTrue(any("akmod-nvidia" in c for c in commands))
        self.assertTrue(any(c.startswith("# repozitár RPM Fusion Nonfree") for c in commands))
        self.assertTrue(any(c.startswith("# voliteľné") for c in commands))


class RealList(unittest.TestCase):
    """Zoznam v data/hardware/base.toml musí byť platný a úplný."""

    def setUp(self):
        self.plan = hwbase.load(paths.data_dir())

    def test_loads(self):
        self.assertEqual(self.plan.id, "latteos-base")
        self.assertTrue(self.plan.groups)

    def test_every_third_party_repo_says_how_it_is_enabled(self):
        """Podpora znamená, že cesta zostáva otvorená aj na stroji, ktorý repozitár nepoužije."""
        for repo in self.plan.repos.values():
            self.assertTrue(repo.release, repo.id)
            self.assertTrue(repo.url.endswith(".rpm"), repo.id)
            self.assertTrue(repo.enable_command().startswith("dnf install http"), repo.id)
            self.assertTrue(repo.note, repo.id)

    def test_every_group_has_a_reason_and_required_packages(self):
        for group in self.plan.groups:
            self.assertTrue(group.why, group.id)
            self.assertTrue(group.required(), group.id)

    def test_device_groups_exist_in_hardware(self):
        from latte_common import hardware
        for group in self.plan.groups:
            for gid in group.devices:
                self.assertIn(gid, hardware.GROUPS, "%s -> %s" % (group.id, gid))

    def test_no_duplicate_packages(self):
        names = [p.name for p in self.plan.packages()]
        self.assertEqual(len(names), len(set(names)), "balík je v zozname dvakrát")

    def test_third_party_packages_are_optional(self):
        for package in self.plan.packages():
            if package.repo:
                self.assertFalse(package.required, "%s je z cudzieho repozitára a nesmie byť povinný" % package.name)

    def test_readme_hardware_base_is_covered(self):
        names = {p.name for p in self.plan.packages()}
        for name in ("mesa-dri-drivers", "mesa-vulkan-drivers", "vulkan-loader", "linux-firmware",
                     "alsa-sof-firmware", "alsa-ucm", "pipewire", "wireplumber", "pipewire-pulseaudio",
                     "libinput", "libwacom", "NetworkManager-wifi", "bluez", "fwupd",
                     "xdg-desktop-portal", "xdg-desktop-portal-gtk", "flatpak", "cups"):
            self.assertIn(name, names, "README ho sľubuje, v latteos-base chýba")


if __name__ == "__main__":
    unittest.main()
