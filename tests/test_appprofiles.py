import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import appprofiles  # noqa: E402

TOOLKITS = """
[toolkit.gtk4]
name = "GTK4"
level = "aligned"
[toolkit.wine]
name = "Wine"
level = "unavailable"
fallback = ["compat", "badge"]
[toolkit.unknown]
name = "Neznáma"
level = "unavailable"
fallback = ["frame", "badge"]
"""


def write(directory, name, text):
    with open(os.path.join(directory, name), "w", encoding="utf-8") as f:
        f.write(text)


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        write(self.tmp.name, "toolkits.toml", TOOLKITS)

    def test_app_inherits_level_and_fallback_from_toolkit(self):
        write(self.tmp.name, "editor.toml", '[profile]\nid="editor"\nname="Editor"\nmatch=["org.x.Editor"]\ntoolkit="gtk4"\n')
        profiles = appprofiles.load([self.tmp.name])
        profile = profiles.for_app("org.x.Editor")
        self.assertEqual((profile.level, profile.fallback, profile.badge), ("aligned", (), None))
        self.assertEqual(profiles.problems, [])

    def test_app_can_override_level_and_fallback(self):
        write(self.tmp.name, "game.toml", '[profile]\nid="game"\nname="Hra"\nmatch=["game*"]\ntoolkit="gtk4"\n'
                                          'level="unavailable"\nfallback=["badge"]\n')
        profile = appprofiles.load([self.tmp.name]).for_app("Game-Launcher")      # veľkosť písmen sa nerozlišuje
        self.assertEqual(profile.id, "game")
        self.assertEqual(profile.badge, "vlastný vzhľad")

    def test_unknown_app_falls_back_to_toolkit_then_to_unknown(self):
        profiles = appprofiles.load([self.tmp.name])
        self.assertEqual(profiles.for_app("nieco", toolkit="wine").id, "wine")
        self.assertEqual(profiles.for_app("nieco").id, "unknown")
        self.assertEqual(profiles.for_app(None).id, "unknown")
        self.assertEqual(profiles.for_app("nieco", toolkit="neexistuje").id, "unknown")

    def test_badge_only_where_system_cannot_enforce(self):
        profiles = appprofiles.load([self.tmp.name])
        self.assertIsNone(profiles.toolkits["gtk4"].badge)
        self.assertEqual(profiles.toolkits["wine"].badge, appprofiles.BADGE_TEXT)

    def test_broken_profile_is_skipped_and_reported(self):
        write(self.tmp.name, "a.toml", '[profile]\nid="a"\nname="A"\nmatch=["a"]\ntoolkit="gtk4"\nlevel="silne"\n')
        write(self.tmp.name, "b.toml", '[profile]\nid="b"\nname="B"\nmatch=["b"]\ntoolkit="qt5"\n')
        write(self.tmp.name, "c.toml", "toto nie je toml [")
        write(self.tmp.name, "d.toml", '[profile]\nid="d"\nname="D"\nmatch=[]\ntoolkit="gtk4"\n')
        write(self.tmp.name, "e.toml", '[profile]\nid="e"\nname="E"\nmatch=["e"]\ntoolkit="gtk4"\nfallback=["blur"]\n')
        profiles = appprofiles.load([self.tmp.name])
        self.assertEqual(profiles.apps, [])
        self.assertEqual(len(profiles.problems), 5)
        self.assertTrue(any("silne" in p for p in profiles.problems))
        self.assertTrue(any("qt5" in p for p in profiles.problems))

    def test_user_directory_overrides_system_profile(self):
        with tempfile.TemporaryDirectory() as user:
            write(self.tmp.name, "x.toml", '[profile]\nid="x"\nname="X"\nmatch=["x"]\ntoolkit="gtk4"\n')
            write(user, "x.toml", '[profile]\nid="x"\nname="X"\nmatch=["x"]\ntoolkit="gtk4"\nlevel="recommended"\n')
            self.assertEqual(appprofiles.load([self.tmp.name, user]).for_app("x").level, "recommended")

    def test_missing_unknown_toolkit_is_an_error(self):
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaises(appprofiles.ProfileError):
                appprofiles.load([empty])
        write(self.tmp.name, "toolkits.toml", '[toolkit.gtk4]\nname="G"\nlevel="aligned"\n')
        profiles = None
        with self.assertRaises(appprofiles.ProfileError):
            profiles = appprofiles.load([self.tmp.name])
        self.assertIsNone(profiles)


class ShippedProfilesTest(unittest.TestCase):
    def test_shipped_profiles_load_without_problems(self):
        profiles = appprofiles.load()
        self.assertEqual(profiles.problems, [])
        self.assertEqual(profiles.for_app("org.gnome.TextEditor").level, "aligned")
        self.assertEqual(profiles.for_app("org.gnome.Loupe").id, "loupe")
        self.assertEqual(profiles.for_app("foot").toolkit, "terminal")
        self.assertIsNotNone(profiles.for_app("neznama-hra").badge)

    def test_every_shipped_level_and_fallback_is_known(self):
        profiles = appprofiles.load()
        for profile in list(profiles.toolkits.values()) + profiles.apps:
            self.assertIn(profile.level, appprofiles.LEVELS)
            self.assertTrue(set(profile.fallback) <= set(appprofiles.FALLBACKS))


if __name__ == "__main__":
    unittest.main()
