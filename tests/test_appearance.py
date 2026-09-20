import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.dom.minidom

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import appearance as ap, settings  # noqa: E402

THEME = """
[theme]
id = "test"
name = "Skúška"
[shape]
s = 2
m = 3
l = 4
xl = 5
xxl = 6
[dark.colors]
fg = "#EEEEEE"
fg-dim = "#AAAAAA"
accent = "#3366CC"
on-accent = "#FFFFFF"
danger = "#FF5544"
base = "#000011"
terminal = "#001100"
terminal-text = "#00FF00"
corner-right = "#111111"
[dark.tint]
base = "#EEEEEE"
t1 = 0.05
t2 = 0.07
t3 = 0.1
t4 = 0.2
line-soft = 0.05
line = 0.1
outline = 0.15
outline-strong = 0.2
accent = 0.3
[dark.panels]
bar = [10, 10, 10, 0.9]
side = [12, 12, 12, 0.7]
list = [14, 14, 14, 0.95]
detail = [16, 16, 16, 0.9]
popup = [18, 18, 18, 0.95]
segment = [20, 20, 20, 0.8]
tabs = [5, 5, 5, 0.5]
"""


def theme_dir(root, name="test", text=THEME):
    path = os.path.join(root, name)
    os.makedirs(path)
    with open(os.path.join(path, "theme.toml"), "w", encoding="utf-8") as f:
        f.write(text)
    return root


class ColorTest(unittest.TestCase):
    def test_hex_roundtrip_and_errors(self):
        self.assertEqual(ap.parse_hex("#D9913b"), (217, 145, 59))
        self.assertEqual(ap.to_hex((217, 145.4, 59)), "#D9913B")
        for bad in ("D9913B", "#12345", "#GGGGGG", None, 5):
            with self.assertRaises(ap.ThemeError):
                ap.parse_hex(bad)

    def test_contrast_and_readable_text(self):
        self.assertAlmostEqual(ap.contrast((0, 0, 0), (255, 255, 255)), 21.0, places=1)
        self.assertEqual(ap.readable_on("#FFFF00"), ap.DARK_TEXT)
        self.assertEqual(ap.readable_on("#101060"), ap.LIGHT_TEXT)

    def test_alpha_formats(self):
        self.assertEqual(ap.rgba((1, 2, 3), 0.9), "rgba(1,2,3,0.9)")
        self.assertEqual(ap.rgba((1, 2, 3), 1.0), "rgba(1,2,3,1)")
        self.assertEqual(ap.rgba((1, 2, 3), 0.68), "rgba(1,2,3,0.68)")
        self.assertEqual(ap.hex8((255, 0, 128), 0.5), "#FF008080")
        self.assertEqual(ap.hex8((0, 0, 0), 2), "#000000FF")


class ThemePackTest(unittest.TestCase):
    def test_shipped_theme_has_both_variants_and_meets_aa_contrast(self):
        theme = ap.load_theme("latte")
        self.assertEqual(set(theme.variants), {"dark", "light"})
        for scheme, v in theme.variants.items():
            under = (0, 0, 0) if scheme == "dark" else (255, 255, 255)
            for name, (r, g, b, a) in v.panels.items():
                bg = tuple(c * a + u * (1 - a) for c, u in zip((r, g, b), under))
                self.assertGreaterEqual(ap.contrast(ap.parse_hex(v.colors["fg"]), bg), 4.5, "%s fg na %s" % (scheme, name))
                self.assertGreaterEqual(ap.contrast(ap.parse_hex(v.colors["fg-dim"]), bg), 4.5, "%s fg-dim na %s" % (scheme, name))
            acc, on = ap.parse_hex(v.colors["accent"]), ap.parse_hex(v.colors["on-accent"])
            self.assertGreaterEqual(ap.contrast(on, acc), 4.5, "%s text na akcente" % scheme)
            lst = tuple(c * v.panels["list"][3] + u * (1 - v.panels["list"][3]) for c, u in zip(v.panels["list"][:3], under))
            self.assertGreaterEqual(ap.contrast(acc, lst), 4.5, "%s akcent ako text" % scheme)

    def test_dark_variant_is_todays_look(self):
        v = ap.latte_vars(ap.resolve({}))
        self.assertEqual(v["--latte-caramel"], "#D9913B")
        self.assertEqual(v["--latte-panel-side"], "rgba(26,20,16,0.68)")
        self.assertEqual(v["--latte-tint-3"], "rgba(242,234,224,0.14)")
        self.assertEqual(v["--latte-accent-tint"], "rgba(217,145,59,0.36)")
        self.assertEqual(v["--latte-radius-2xl"], "14px")
        self.assertEqual(v["--latte-titlebar-height"], "46px")
        self.assertEqual(len(v), 31)

    def test_broken_packs_are_refused_with_a_reason(self):
        bad = {
            "bez id": THEME.replace('id = "test"\n', ""),
            "zlá farba": THEME.replace('#EEEEEE"\nfg-dim', '#EEE"\nfg-dim'),
            "chýba rola": THEME.replace('danger = "#FF5544"\n', ""),
            "priehľadnosť 2": THEME.replace("t1 = 0.05", "t1 = 2"),
            "panel s 3 hodnotami": THEME.replace("[10, 10, 10, 0.9]", "[10, 10, 10]"),
            "chýba shape": THEME.replace("xxl = 6\n", ""),
            "žiadny variant": THEME.split("[dark.colors]")[0],
        }
        for label, text in bad.items():
            with tempfile.TemporaryDirectory() as tmp:
                theme_dir(tmp, text=text)
                with self.assertRaises(ap.ThemeError, msg=label):
                    ap.load_theme("test", [tmp])

    def test_id_must_match_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            theme_dir(tmp, name="ine")
            with self.assertRaises(ap.ThemeError):
                ap.load_theme("ine", [tmp])

    def test_list_themes_skips_broken_and_user_theme_overrides_system(self):
        with tempfile.TemporaryDirectory() as system, tempfile.TemporaryDirectory() as user:
            theme_dir(system)
            theme_dir(system, "rozbity", "[theme\n")
            theme_dir(user, text=THEME.replace('name = "Skúška"', 'name = "Moja verzia"'))
            themes, problems = ap.list_themes([system, user])
        self.assertEqual([(t.id, t.name) for t in themes], [("test", "Moja verzia")])
        self.assertEqual(len(problems), 1)
        self.assertIn("rozbity", problems[0])


class ResolveTest(unittest.TestCase):
    def test_defaults(self):
        t = ap.resolve({})
        self.assertEqual((t.theme_id, t.scheme, t.accent), ("latte", "dark", "#D9913B"))
        self.assertEqual(t.problems, [])
        self.assertTrue(t.transparency)

    def test_light_variant_switches_every_text_role(self):
        dark, light = ap.resolve({"color.scheme": "dark"}), ap.resolve({"color.scheme": "light"})
        self.assertNotEqual(dark.colors["fg"], light.colors["fg"])
        self.assertGreater(ap.luminance(ap.parse_hex(dark.colors["fg"])), ap.luminance(ap.parse_hex(light.colors["fg"])))

    def test_custom_accent_gets_readable_text(self):
        t = ap.resolve({"color.accent": "#ffe066"})
        self.assertEqual(t.accent, "#FFE066")
        self.assertEqual(t.colors["on-accent"], ap.DARK_TEXT)
        self.assertEqual(ap.latte_vars(t)["--latte-accent-tint"], "rgba(255,224,102,0.36)")
        self.assertEqual(ap.resolve({"color.accent": "#101060"}).colors["on-accent"], ap.LIGHT_TEXT)

    def test_transparency_off_makes_all_panels_opaque(self):
        t = ap.resolve({"color.transparency": False})
        self.assertTrue(all(p[3] == 1.0 for p in t.panels.values()))
        self.assertTrue(all(p[3] < 1.0 for p in ap.resolve({}).panels.values()))
        self.assertNotIn("0.68", ap.css_variables(t))

    def test_square_corners_zero_every_radius(self):
        t = ap.resolve({"shape.corners": "square"})
        self.assertEqual(set(t.radii.values()), {0})
        self.assertIn("--latte-radius-m: 0px;", ap.css_variables(t))

    def test_high_contrast(self):
        t = ap.resolve({"accessibility.contrast": "high"})
        self.assertEqual(t.colors["fg-dim"], t.colors["fg"])
        self.assertTrue(all(p[3] == 1.0 for p in t.panels.values()))
        self.assertGreater(t.tint["outline"], ap.resolve({}).tint["outline"])

    def test_unknown_theme_falls_back_and_says_so(self):
        t = ap.resolve({"theme.id": "neexistuje"})
        self.assertEqual(t.theme_id, "latte")
        self.assertEqual(len(t.problems), 1)
        self.assertIn("neexistuje", t.problems[0])

    def test_missing_variant_falls_back_and_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            theme_dir(tmp)
            t = ap.resolve({"theme.id": "test", "color.scheme": "light"}, [tmp])
        self.assertEqual(t.scheme, "dark")
        self.assertIn("nemá light variant", t.problems[0])


class GeneratorTest(unittest.TestCase):
    def test_gtk4_css_covers_the_libadwaita_variables_that_matter(self):
        css = ap.gtk4_css(ap.resolve({}))
        for var in ("--accent-bg-color", "--window-bg-color", "--headerbar-bg-color", "--headerbar-fg-color",
                    "--sidebar-bg-color", "--popover-bg-color", "--view-bg-color", "--card-bg-color"):
            self.assertIn(var + ":", css)
        self.assertTrue(css.startswith(":root {") and css.rstrip().endswith("}"))

    def test_gtk4_css_carries_both_schemes_and_lets_gtk_choose(self):
        css = ap.gtk4_css(ap.resolve({"color.scheme": "dark"}))
        self.assertEqual(css.count(":root {"), 2)
        self.assertIn("@media (prefers-color-scheme: dark)", css)
        base, dark = css.split("@media")
        self.assertIn("--window-fg-color: #2B211A;", base)          # základ = svetlý variant
        self.assertIn("--window-fg-color: #F2EAE0;", dark)          # tmavý sa zapne médiom
        # zvolený režim nemení obsah súboru: prepína ho portál za behu, nie prepísanie gtk.css
        self.assertEqual(css, ap.gtk4_css(ap.resolve({"color.scheme": "light"})))

    def test_gtk4_css_of_a_single_variant_theme_has_no_media_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            theme_dir(tmp)
            css = ap.gtk4_css(ap.resolve({"theme.id": "test"}, [tmp]))
        self.assertNotIn("@media", css)
        self.assertEqual(css.count(":root {"), 1)

    def test_custom_accent_reaches_both_variants(self):
        css = ap.gtk4_css(ap.resolve({"color.accent": "#3A9BD9"}))
        self.assertEqual(css.count("--accent-bg-color: #3A9BD9;"), 2)

    def test_gtk_ini_values(self):
        ini = ap.gtk_ini(ap.resolve({"color.scheme": "light", "font.family": "Inter", "font.scale": 1.25, "window.buttons": "close"}))
        self.assertEqual(ini["gtk-application-prefer-dark-theme"], "false")
        self.assertEqual(ini["gtk-font-name"], "Inter 11")
        self.assertEqual(ini["gtk-xft-dpi"], "122880")
        self.assertEqual(ini["gtk-decoration-layout"], ":close")
        plain = ap.gtk_ini(ap.resolve({}))
        self.assertIsNone(plain["gtk-font-name"])
        self.assertIsNone(plain["gtk-xft-dpi"])

    def test_labwc_theme_uses_only_real_labwc_keys(self):
        text = ap.labwc_theme(ap.resolve({}))
        keys = [line.split(":", 1)[0] for line in text.splitlines() if line and not line.startswith("#")]
        self.assertGreater(len(keys), 25)
        for line in text.splitlines():
            if line and not line.startswith("#"):
                key, value = line.split(": ", 1)
                if key.endswith("color"):
                    self.assertRegex(value, r"^#[0-9A-F]{6}([0-9A-F]{2})?$", key)
        if shutil.which("man"):
            page = subprocess.run(["man", "-P", "cat", "labwc-theme"], capture_output=True, text=True).stdout
            if page:
                for key in keys:
                    self.assertIn(key, page, "labwc-theme nepozná kľúč %s" % key)

    def test_portal_values(self):
        dark = ap.portal_values(ap.resolve({}))
        self.assertEqual(dark["org.freedesktop.appearance"]["color-scheme"], ("u", 1))
        self.assertEqual(ap.portal_values(ap.resolve({"color.scheme": "light"}))["org.freedesktop.appearance"]["color-scheme"], ("u", 2))
        sig, (r, g, b) = dark["org.freedesktop.appearance"]["accent-color"]
        self.assertEqual(sig, "(ddd)")
        self.assertAlmostEqual(r, 217 / 255)
        self.assertEqual(dark["org.freedesktop.appearance"]["contrast"], ("u", 0))
        self.assertEqual(dark["org.gnome.desktop.interface"]["color-scheme"], ("s", "prefer-dark"))
        self.assertEqual(dark["org.gnome.desktop.wm.preferences"]["button-layout"], ("s", ":minimize,maximize,close"))
        self.assertNotIn("font-name", dark["org.gnome.desktop.interface"])
        self.assertEqual(ap.portal_values(ap.resolve({"font.family": "Inter"}))["org.gnome.desktop.interface"]["font-name"], ("s", "Inter 11"))
        self.assertEqual(ap.portal_values(ap.resolve({"accessibility.contrast": "high"}))["org.freedesktop.appearance"]["contrast"], ("u", 1))


class ManagedFilesTest(unittest.TestCase):
    def test_block_keeps_user_css_and_is_idempotent(self):
        user = "/* moje */\nwindow { border: 1px solid red; }\n"
        once = ap.merge_block(user, ":root { --a: 1; }\n")
        self.assertTrue(once.startswith(user))
        self.assertEqual(ap.merge_block(once, ":root { --a: 1; }\n"), once)
        twice = ap.merge_block(once, ":root { --a: 2; }\n")
        self.assertIn("--a: 2", twice)
        self.assertNotIn("--a: 1", twice)
        self.assertEqual(twice.count(ap.BLOCK_BEGIN), 1)
        self.assertEqual(ap.strip_block(twice), user)
        self.assertEqual(ap.find_block(twice), ":root { --a: 2; }\n")

    def test_block_in_empty_or_missing_file(self):
        block = ap.merge_block("", "x\n")
        self.assertEqual(ap.strip_block(block), "")
        self.assertIsNone(ap.find_block("nič"))

    def test_ini_merge_preserves_everything_else(self):
        text = "# komentár\n[Settings]\ngtk-cursor-theme-name=Adwaita\ngtk-application-prefer-dark-theme=false\n\n[Iné]\nx=1\n"
        out = ap.merge_ini(text, {"gtk-application-prefer-dark-theme": "true", "gtk-font-name": "Inter 11", "gtk-xft-dpi": None})
        data = ap.parse_ini(out)
        self.assertEqual(data["Settings"]["gtk-cursor-theme-name"], "Adwaita")
        self.assertEqual(data["Settings"]["gtk-application-prefer-dark-theme"], "true")
        self.assertEqual(data["Settings"]["gtk-font-name"], "Inter 11")
        self.assertEqual(data["Iné"], {"x": "1"})
        self.assertIn("# komentár", out)
        self.assertEqual(ap.merge_ini(out, {"gtk-application-prefer-dark-theme": "true", "gtk-font-name": "Inter 11", "gtk-xft-dpi": None}), out)

    def test_ini_without_settings_section_and_removal(self):
        out = ap.merge_ini("", {"gtk-font-name": "A 11"})
        self.assertEqual(out, "[Settings]\ngtk-font-name=A 11\n")
        self.assertNotIn("gtk-font-name", ap.merge_ini(out, {"gtk-font-name": None}))
        only_other = ap.merge_ini("[Other]\na=1\n", {"k": "v"})
        self.assertEqual(ap.parse_ini(only_other), {"Other": {"a": "1"}, "Settings": {"k": "v"}})


class WindowButtonsTest(unittest.TestCase):
    """Tlačidlá okien majú v každej vrstve (GTK, libadwaita, rám labwc) rovnaký rozmer, tvar a odstup."""

    def setUp(self):
        self.dark = ap.resolve({"color.scheme": "dark"})

    def test_labwc_gets_svg_for_every_button_state(self):
        files = ap.labwc_buttons(self.dark)
        self.assertEqual(len(files), len(ap.BUTTON_KINDS) * 2)
        self.assertIn("close-active.svg", files)
        self.assertIn("max_toggled-inactive.svg", files)
        for name, svg in files.items():
            xml.dom.minidom.parseString(svg)                        # platný XML
            self.assertIn('width="%d" height="%d"' % (ap.BUTTON_WIDTH, ap.BUTTON_HEIGHT), svg, name)

    def test_active_and_inactive_icons_follow_theme_colors(self):
        files = ap.labwc_buttons(self.dark)
        self.assertIn('fill="%s"' % self.dark.colors["fg"], files["iconify-active.svg"])
        self.assertIn('fill="%s"' % self.dark.colors["fg-dim"], files["iconify-inactive.svg"])
        light = ap.labwc_buttons(ap.resolve({"color.scheme": "light"}))
        self.assertNotEqual(light["close-active.svg"], files["close-active.svg"])

    def test_labwc_geometry_matches_gtk_css(self):
        theme = ap.labwc_theme(self.dark)
        css = ap.window_controls_css(self.dark)
        self.assertIn("window.button.width: %d" % ap.BUTTON_WIDTH, theme)
        self.assertIn("window.button.spacing: %d" % ap.BUTTON_SPACING, theme)
        self.assertIn("min-width: %dpx" % ap.BUTTON_WIDTH, css)
        self.assertIn("margin: 0 %dpx" % (ap.BUTTON_SPACING // 2), css)
        self.assertIn("border-radius: %dpx" % self.dark.radii["m"], css)
        self.assertIn("window.button.hover.bg.corner-radius: %d" % self.dark.radii["m"], theme)

    def test_libadwaita_circle_is_removed_where_it_is_drawn(self):
        css = ap.window_controls_css(self.dark)
        self.assertIn("windowcontrols > button > image {\n    background: none;", css)   # kruh je na obrázku, nie na tlačidle
        self.assertNotIn("rgba(", css)                              # nezávisí od režimu: gtk.css sa pri jeho prepnutí nemení

    def test_theme_files_go_to_the_named_labwc_theme(self):
        with tempfile.TemporaryDirectory() as root:
            dirs = ap.Dirs(config_home=os.path.join(root, "cfg"), labwc=os.path.join(root, "cfg", "labwc"),
                           data_home=os.path.join(root, "share"))
            actions = ap.plan(self.dark, dirs)
            ap.apply(actions)
            folder = os.path.join(root, "share", "themes", ap.LABWC_THEME, "labwc")
            self.assertEqual(dirs.labwc_theme, folder)
            self.assertTrue(os.path.exists(os.path.join(folder, "close-active.svg")))
            self.assertTrue(os.path.exists(os.path.join(folder, "themerc")))
            changed = ap.release(actions)
            self.assertIn(os.path.join(folder, "close-active.svg"), changed)
            self.assertFalse(os.path.exists(os.path.join(folder, "close-active.svg")))

    def test_one_titlebar_height_reaches_every_layer(self):
        for height in (46, 52, 64):
            t = ap.resolve({"window.titlebar": height})
            self.assertEqual(t.titlebar, height)
            self.assertEqual(ap.latte_vars(t)["--latte-titlebar-height"], "%dpx" % height)
            self.assertIn("min-height: %dpx" % height, ap.gtk4_css(t))
            padding = int(re.search(r"window\.titlebar\.padding\.height: (\d+)", ap.labwc_theme(t)).group(1))
            self.assertEqual(ap.BUTTON_HEIGHT + 2 * padding, height - height % 2 + (ap.BUTTON_HEIGHT % 2))

    def test_titlebar_css_spares_own_components_and_corrects_collapsed_spacing(self):
        css = ap.titlebar_css(ap.resolve({"window.titlebar": 52}))
        self.assertIn("headerbar:not(.latte-titlebar) {\n    min-height: 52px;", css)
        self.assertIn("toolbarview > .top-bar .collapse-spacing headerbar:not(.latte-titlebar) {\n    min-height: %dpx;"
                      % (52 - ap.COLLAPSED_SPACING_EXTRA), css)
        # pod minimom sa nejde (libadwaita hlavička sa nezmenší)
        self.assertIn("min-height: %dpx;" % ap.MIN_TITLEBAR, ap.titlebar_css(ap.Tokens(**{**ap.resolve({}).__dict__, "titlebar": 10})))

    def test_own_titlebar_class_is_used_by_the_file_manager_and_styled_by_latte_css(self):
        root = os.path.join(os.path.dirname(__file__), "..")
        with open(os.path.join(root, "src", "latte_files", "app.py"), encoding="utf-8") as f:
            self.assertIn('add_css_class("latte-titlebar")', f.read())
        with open(os.path.join(root, "data", "styles", "latte.css"), encoding="utf-8") as f:
            self.assertIn("headerbar.latte-titlebar { min-height: calc(var(--latte-titlebar-height)", f.read())

    def test_titlebar_height_is_validated_by_the_schema(self):
        key = settings.Registry().domain("appearance").key("window.titlebar")
        self.assertEqual(key.default, ap.DEFAULT_TITLEBAR)
        self.assertEqual(key.validate(50), 50)
        for bad in (10, 200, "vysoké"):
            with self.assertRaises(settings.SettingsError):
                key.validate(bad)

    def test_shipped_rc_xml_selects_the_generated_theme(self):
        rc = os.path.join(os.path.dirname(__file__), "..", "session", "labwc", "rc.xml")
        name = xml.dom.minidom.parse(rc).getElementsByTagName("theme")[0].getElementsByTagName("name")[0]
        self.assertEqual(name.firstChild.data, ap.LABWC_THEME)


class PlanTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = self._tmp.name
        self.dirs = ap.Dirs(config_home=os.path.join(root, "cfg"), labwc=os.path.join(root, "cfg", "labwc"))
        self.tokens = ap.resolve({})

    def tearDown(self):
        self._tmp.cleanup()

    def test_apply_writes_everything_once_then_nothing(self):
        actions = ap.plan(self.tokens, self.dirs)
        self.assertEqual(len(ap.apply(actions)), len(actions))
        self.assertEqual({s for _a, _p, s in ap.check(actions)}, {"ok"})
        self.assertEqual(ap.apply(actions), [])                       # idempotentné

    def test_missing_and_drift_are_detected_and_repaired(self):
        actions = ap.plan(self.tokens, self.dirs)
        self.assertEqual({s for _a, _p, s in ap.check(actions)}, {"missing"})
        ap.apply(actions)
        css = os.path.join(self.dirs.config_home, "gtk-4.0", "gtk.css")
        with open(css, encoding="utf-8") as f:
            edited = f.read().replace("--window-fg-color", "--window-fg-colour")
        with open(css, "w", encoding="utf-8") as f:
            f.write(edited)
        states = {os.path.basename(p): s for _a, p, s in ap.check(actions)}
        self.assertEqual(states["gtk.css"], "drift")
        self.assertEqual(states["themerc-override"], "ok")
        self.assertEqual(ap.apply(actions), [css])
        self.assertEqual({s for _a, _p, s in ap.check(actions)}, {"ok"})

    def test_user_gtk_css_outside_the_block_is_untouched(self):
        css = os.path.join(self.dirs.config_home, "gtk-4.0", "gtk.css")
        os.makedirs(os.path.dirname(css))
        with open(css, "w", encoding="utf-8") as f:
            f.write("/* moje pravidlá */\nbutton { color: pink; }\n")
        ap.apply(ap.plan(self.tokens, self.dirs))
        ap.apply(ap.plan(ap.resolve({"color.scheme": "light"}), self.dirs))
        with open(css, encoding="utf-8") as f:
            text = f.read()
        self.assertTrue(text.startswith("/* moje pravidlá */\nbutton { color: pink; }\n"))
        self.assertEqual(text.count(ap.BLOCK_BEGIN), 1)

    def test_scheme_switch_leaves_gtk_css_alone(self):
        ap.apply(ap.plan(ap.resolve({"color.scheme": "dark"}), self.dirs))
        changed = ap.apply(ap.plan(ap.resolve({"color.scheme": "light"}), self.dirs))
        names = {os.path.basename(p) for p in changed}
        self.assertNotIn("gtk.css", names)
        self.assertLessEqual({"settings.ini", "themerc-override"}, names)

    def test_settings_change_changes_only_affected_files(self):
        ap.apply(ap.plan(self.tokens, self.dirs))
        changed = ap.apply(ap.plan(ap.resolve({"window.buttons": "close"}), self.dirs))
        self.assertEqual({os.path.basename(p) for p in changed}, {"settings.ini"})

    def test_release_removes_only_what_latteos_owns(self):
        css = os.path.join(self.dirs.config_home, "gtk-4.0", "gtk.css")
        ini = os.path.join(self.dirs.config_home, "gtk-4.0", "settings.ini")
        os.makedirs(os.path.dirname(css))
        with open(css, "w", encoding="utf-8") as f:
            f.write("button { color: pink; }\n")
        with open(ini, "w", encoding="utf-8") as f:
            f.write("[Settings]\ngtk-cursor-theme-name=Adwaita\n")
        actions = ap.plan(ap.resolve({"font.family": "Inter"}), self.dirs)
        ap.apply(actions)
        self.assertGreater(len(ap.release(actions)), 0)
        with open(css, encoding="utf-8") as f:
            self.assertEqual(f.read(), "button { color: pink; }\n")
        self.assertEqual(ap.parse_ini(open(ini, encoding="utf-8").read()), {"Settings": {"gtk-cursor-theme-name": "Adwaita"}})
        self.assertFalse(os.path.exists(os.path.join(self.dirs.labwc, "themerc-override")))
        self.assertFalse(os.path.exists(os.path.join(self.dirs.config_home, "gtk-3.0", "settings.ini")))

    def test_apply_works_through_a_symlinked_config_directory(self):
        real = os.path.join(self._tmp.name, "repo-labwc")
        os.makedirs(real)
        os.makedirs(self.dirs.config_home)
        os.symlink(real, self.dirs.labwc)
        ap.apply(ap.plan(self.tokens, self.dirs))
        self.assertTrue(os.path.isfile(os.path.join(real, "themerc-override")))


if __name__ == "__main__":
    unittest.main()
