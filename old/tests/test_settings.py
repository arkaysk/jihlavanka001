import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import settings  # noqa: E402

def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


SCHEMA = {
    "domain": {"id": "demo", "title": "Ukážka", "file": "demo.toml"},
    "section": {"color": {"title": "Farby"}},
    "key": {
        "color.scheme": {"type": "enum", "choices": ["dark", "light"], "default": "dark", "label": "Režim"},
        "color.accent": {"type": "color", "default": "", "allow_empty": True},
        "color.blur": {"type": "bool", "default": True},
        "font.scale": {"type": "float", "default": 1.0, "min": 0.8, "max": 1.6},
        "font.size": {"type": "int", "default": 11, "min": 6, "max": 40},
        "wallpaper.path": {"type": "path", "default": "", "allow_empty": True},
        "zones": {"type": "string", "default": "UTC", "allow_empty": True},
        "secret": {"type": "string", "default": "x", "hidden": True},
    },
}


class KeyValidationTest(unittest.TestCase):
    def setUp(self):
        self.domain = settings.parse_domain(SCHEMA)

    def check(self, key, value):
        return self.domain.key(key).validate(value)

    def test_valid_values_are_canonical(self):
        self.assertEqual(self.check("color.accent", "#d9913b"), "#D9913B")
        self.assertEqual(self.check("font.scale", 1), 1.0)
        self.assertIsInstance(self.check("font.scale", 1), float)
        self.assertEqual(self.check("font.size", 12.0), 12)
        self.assertEqual(self.check("wallpaper.path", "/home/u/a b.jpg"), "/home/u/a b.jpg")

    def test_invalid_values_are_refused_with_a_reason(self):
        for key, value in [("color.scheme", "blue"), ("color.accent", "red"), ("color.accent", "#12345"),
                           ("font.scale", 2.0), ("font.scale", "1"), ("font.size", 5), ("font.size", 11.5),
                           ("color.blur", 1), ("color.blur", "yes"), ("wallpaper.path", "relative/x.jpg"),
                           ("zones", None), ("zones", "a\0b"), ("font.size", True)]:
            with self.assertRaises(settings.SettingsError, msg="%s=%r" % (key, value)):
                self.check(key, value)

    def test_empty_is_only_allowed_where_declared(self):
        self.assertEqual(self.check("color.accent", ""), "")
        with self.assertRaises(settings.SettingsError):
            self.check("color.scheme", "")

    def test_unknown_key(self):
        with self.assertRaises(settings.SettingsError):
            self.domain.key("nie.je")

    def test_key_parts_and_grouping(self):
        key = self.domain.key("color.scheme")
        self.assertEqual((key.section, key.name), ("color", "scheme"))
        self.assertEqual((self.domain.key("zones").section, self.domain.key("zones").name), ("", "zones"))
        groups = {name: [k.id for k in keys] for name, _t, keys in self.domain.grouped()}
        self.assertNotIn("secret", [k for ids in groups.values() for k in ids])     # hidden
        self.assertEqual(groups["color"], ["color.scheme", "color.accent", "color.blur"])


class SchemaValidationTest(unittest.TestCase):
    def bad(self, mutate):
        data = {"domain": dict(SCHEMA["domain"]), "key": {k: dict(v) for k, v in SCHEMA["key"].items()}}
        mutate(data)
        with self.assertRaises(settings.SettingsError):
            settings.parse_domain(data)

    def test_rejects_broken_schemas(self):
        self.bad(lambda d: d["domain"].pop("file"))
        self.bad(lambda d: d["domain"].update(id="Zle Meno"))
        self.bad(lambda d: d["domain"].update(file="../x.toml"))
        self.bad(lambda d: d["key"]["zones"].update(type="magic"))
        self.bad(lambda d: d["key"]["zones"].pop("default"))
        self.bad(lambda d: d["key"]["color.scheme"].update(default="green"))       # default mimo choices
        self.bad(lambda d: d["key"]["color.scheme"].pop("choices"))
        self.bad(lambda d: d["key"]["zones"].update(apply="kedykolvek"))
        self.bad(lambda d: d["key"].update({"a.b.c": {"type": "bool", "default": True}}))

    def test_shipped_schemas_are_valid_and_consistent(self):
        registry = settings.Registry()
        self.assertIn("appearance", registry.domains)
        for domain in registry.domains.values():
            for key in domain.keys.values():
                self.assertEqual(key.validate(key.default), key.default, "%s.%s" % (domain.id, key.id))
                self.assertTrue(key.label, "%s.%s nemá label" % (domain.id, key.id))
        self.assertEqual(len({p.id for p in registry.pages}), len(registry.pages))
        for gid, _title, pages in registry.by_group():
            self.assertIn(gid, registry.groups)
        ready = [p for p in registry.pages if p.status == "ready"]
        self.assertTrue(all(p.domain or p.view for p in ready), "stránka „ready“ musí mať doménu alebo vlastný obsah")

    def test_tree_follows_the_six_areas_of_the_design(self):
        registry = settings.Registry()
        self.assertEqual(list(registry.groups), ["software", "data", "hardware", "account", "environment", "system"])
        for gid in registry.groups:
            self.assertTrue(registry.area_pages(gid), "oblasť %s je prázdna" % gid)
            self.assertTrue(registry.group_notes[gid], "oblasť %s nemá popis" % gid)
        for page in registry.pages:
            self.assertTrue(page.description, "%s nemá popis" % page.id)
            if page.status == "planned":
                self.assertTrue(page.contents, "plánovaná stránka %s musí povedať, čo bude obsahovať" % page.id)

    def test_pages_of_one_domain_do_not_share_a_section(self):
        registry = settings.Registry()
        seen = {}
        for page in registry.pages:
            for section, _title, keys in registry.page_sections(page):
                for key in keys:
                    self.assertNotIn(key.id, seen, "%s je na stránkach %s aj %s" % (key.id, seen.get(key.id), page.id))
                    seen[key.id] = page.id
        # každé viditeľné nastavenie Prispôsobenia je niekde v Nastaveniach
        for key in registry.domain("appearance").keys.values():
            if not key.hidden:
                self.assertIn(key.id, seen)

    def test_page_uri_and_resolve(self):
        registry = settings.Registry()
        page = registry.page("theme")
        self.assertEqual(page.uri, "settings://environment/theme")
        self.assertEqual(registry.resolve(page.uri), ("page", page))
        self.assertEqual(registry.resolve("environment/theme"), ("page", page))
        self.assertEqual(registry.resolve("theme"), ("page", page))
        self.assertEqual(registry.resolve("settings://hardware"), ("area", "hardware"))
        for bad in ("", None, "settings://", "hardware/theme", "a/b/c", "nie-je"):
            self.assertIsNone(registry.resolve(bad), repr(bad))

    def test_choice_labels_match_choices(self):
        registry = settings.Registry()
        scheme = registry.domain("appearance").key("color.scheme")
        self.assertEqual(scheme.choice_label("light"), "Svetlý")
        self.assertEqual(scheme.choice_label("neznáme"), "neznáme")
        for domain in registry.domains.values():
            for key in domain.keys.values():
                if key.type == "enum":
                    self.assertEqual(len(key.choice_labels), len(key.choices), key.id)

    def test_labels_with_wrong_count_are_refused(self):
        data = {"domain": SCHEMA["domain"], "key": {"a": {"type": "enum", "choices": ["x", "y"], "labels": ["X"], "default": "x"}}}
        with self.assertRaises(settings.SettingsError):
            settings.parse_domain(data)

    def test_page_with_unknown_section_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            for name in os.listdir(settings.schema_dir()):
                with open(os.path.join(settings.schema_dir(), name), "rb") as src, open(os.path.join(d, name), "wb") as dst:
                    dst.write(src.read())
            with open(os.path.join(d, "index.toml"), "a", encoding="utf-8") as f:
                f.write('\n[[page]]\nid = "zle"\ntitle = "Zlé"\ngroup = "system"\ndomain = "appearance"\nsections = ["nie-je"]\n')
            with self.assertRaises(settings.SettingsError):
                settings.Registry(d)

    def registry_with_page(self, extra):
        """Registry z dočasnej kópie schém a indexu s jednou pridanou stránkou."""
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        for name in os.listdir(settings.schema_dir()):
            with open(os.path.join(settings.schema_dir(), name), "rb") as src, open(os.path.join(d, name), "wb") as dst:
                dst.write(src.read())
        with open(os.path.join(d, "index.toml"), "a", encoding="utf-8") as f:
            f.write("\n[[page]]\nid = \"nova\"\ntitle = \"Nová\"\ngroup = \"system\"\n" + extra)
        return d

    def test_bar_page_shows_the_height_before_its_own_settings(self):
        registry = settings.Registry()
        found = [(k.domain, k.id) for _s, _t, keys in registry.page_sections(registry.page("bar")) for k in keys]
        self.assertEqual(found[0], ("appearance", "bar.height"))
        self.assertIn(("prompt", "ai_url"), found)
        self.assertEqual([d for d, _s in registry.page_sources(registry.page("bar"))], ["appearance", "appearance", "prompt"])
        self.assertIn(("appearance", "bars.left"), found)
        self.assertIn(("appearance", "bars.dim"), found)

    def test_bar_height_is_a_slider_with_a_range(self):
        key = settings.Registry().domain("appearance").key("bar.height")
        self.assertEqual((key.type, key.control, key.unit), ("int", "slider", "px"))
        self.assertLess(key.minimum, key.default)
        self.assertLess(key.default, key.maximum + 1)

    def test_include_needs_a_known_domain_and_section_and_an_own_domain(self):
        for extra in ('domain = "prompt"\ninclude = ["nie-je:bar"]\n',
                      'domain = "prompt"\ninclude = ["appearance:nie-je"]\n',
                      'domain = "appearance"\ninclude = ["appearance:bar"]\n',
                      'include = ["appearance:bar"]\n'):
            with self.assertRaises(settings.SettingsError, msg=extra):
                settings.Registry(self.registry_with_page(extra))

    def test_slider_needs_a_numeric_key_with_a_range(self):
        def schema(**key):
            return {"domain": SCHEMA["domain"], "key": {"a": dict({"default": 1, "control": "slider"}, **key)}}
        settings.parse_domain(schema(type="int", min=0, max=10))
        for bad in (schema(type="int"), schema(type="int", min=0), schema(type="string", default="x"),
                    schema(type="int", min=0, max=5, control="dial")):
            with self.assertRaises(settings.SettingsError):
                settings.parse_domain(bad)


class StoreTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = os.path.join(self._tmp.name, "user")
        self.admin = os.path.join(self._tmp.name, "admin")
        self.domain = settings.parse_domain(SCHEMA)

    def tearDown(self):
        self._tmp.cleanup()

    def store(self):
        return settings.Store(self.domain, self.dir, self.admin)

    def test_defaults_without_file(self):
        s = self.store()
        self.assertEqual(s.get("color.scheme"), "dark")
        self.assertEqual(s.source("color.scheme"), "default")
        self.assertEqual(s.explicit(), {})
        self.assertFalse(os.path.exists(s.path))

    def test_set_persists_and_roundtrips_odd_text(self):
        s = self.store()
        s.set_many({"color.scheme": "light", "wallpaper.path": '/home/čučo/"foto" (2)\\a.jpg', "zones": "A/B,C/D", "font.scale": 1.25})
        again = self.store()
        self.assertEqual(again.get("color.scheme"), "light")
        self.assertEqual(again.get("wallpaper.path"), '/home/čučo/"foto" (2)\\a.jpg')
        self.assertEqual(again.get("font.scale"), 1.25)
        self.assertEqual(again.source("zones"), "user")
        self.assertEqual(again.problems, [])

    def test_invalid_set_writes_nothing(self):
        s = self.store()
        s.set("color.scheme", "light")
        before = read(s.path)
        with self.assertRaises(settings.SettingsError):
            s.set_many({"color.blur": False, "color.scheme": "neon"})
        self.assertEqual(read(s.path), before)
        self.assertTrue(self.store().get("color.blur"))

    def test_reset_returns_default_and_prunes_empty_sections(self):
        s = self.store()
        s.set_many({"color.scheme": "light", "zones": "X/Y"})
        s.reset("color.scheme")
        s = self.store()
        self.assertEqual(s.get("color.scheme"), "dark")
        self.assertEqual(s.get("zones"), "X/Y")
        self.assertNotIn("[color]", read(s.path))
        s.reset("zones")
        self.assertEqual(self.store().explicit(), {})

    def test_unknown_keys_and_sections_survive_a_write(self):
        os.makedirs(self.dir)
        with open(os.path.join(self.dir, "demo.toml"), "w") as f:
            f.write('novy_kluc = "budúcnosť"\n[color]\nscheme = "light"\nextra = 5\n[cudzia]\na = 1\n')
        s = self.store()
        s.set("color.blur", False)
        text = read(s.path)
        for needle in ('novy_kluc = "budúcnosť"', "extra = 5", "[cudzia]", 'scheme = "light"', "blur = false"):
            self.assertIn(needle, text)

    def test_broken_file_falls_back_and_reports(self):
        os.makedirs(self.dir)
        with open(os.path.join(self.dir, "demo.toml"), "w") as f:
            f.write("[color\nscheme = ")
        s = self.store()
        self.assertEqual(s.get("color.scheme"), "dark")
        self.assertEqual(len(s.problems), 1)
        self.assertIn("demo.toml", s.problems[0])

    def test_invalid_value_in_file_is_ignored_and_reported(self):
        os.makedirs(self.dir)
        with open(os.path.join(self.dir, "demo.toml"), "w") as f:
            f.write('[color]\nscheme = "neon"\nblur = false\n[font]\nscale = 9.0\n')
        s = self.store()
        self.assertEqual(s.get("color.scheme"), "dark")
        self.assertFalse(s.get("color.blur"))                  # platný kľúč sa použije
        self.assertEqual(s.get("font.scale"), 1.0)
        self.assertEqual(len(s.problems), 2)

    def test_admin_layer_wins_and_cannot_be_changed(self):
        os.makedirs(self.admin)
        with open(os.path.join(self.admin, "demo.toml"), "w") as f:
            f.write('[color]\nscheme = "light"\n')
        s = self.store()
        s.set("zones", "Q/R")                                   # iný kľúč sa zapísať dá
        self.assertEqual(s.get("color.scheme"), "light")
        self.assertEqual(s.source("color.scheme"), "admin")
        self.assertTrue(s.locked("color.scheme"))
        with self.assertRaises(settings.SettingsError):
            s.set("color.scheme", "dark")
        self.assertEqual(s.get("zones"), "Q/R")

    def test_values_lists_every_key(self):
        self.assertEqual(set(self.store().values()), set(SCHEMA["key"]))


class DumpsTest(unittest.TestCase):
    def test_roundtrip_through_tomllib(self):
        import tomllib
        data = {"a": 1, "b": "x\ny\"z", "c": 1.5, "d": True, "l": ["q", "r"], "sec": {"k": "v", "n": {"deep": 2}}, "empty": {}}
        back = tomllib.loads(settings.dumps(data, "# hlavička"))
        self.assertEqual(back["a"], 1)
        self.assertEqual(back["b"], "x\ny\"z")
        self.assertEqual(back["sec"], {"k": "v", "n": {"deep": 2}})
        self.assertEqual(back["l"], ["q", "r"])

    def test_refuses_nan(self):
        with self.assertRaises(settings.SettingsError):
            settings.dumps({"x": float("nan")})


if __name__ == "__main__":
    unittest.main()
