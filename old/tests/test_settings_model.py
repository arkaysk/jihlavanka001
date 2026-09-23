import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from latte_common import settings  # noqa: E402
from latte_settings import model  # noqa: E402

FACTS = {"user": "kava", "release": "DEV", "name": "LatteOS", "scheme": "dark", "problems": 0,
         "free": 60 * 10**9, "total": 100 * 10**9}


class SearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = settings.Registry()
        cls.index = model.build_index(cls.registry)

    def titles(self, query):
        return [h.title for h in model.search(self.index, query)]

    def test_synonym_finds_the_page(self):
        self.assertEqual(self.titles("wifi")[0], "Sieť")
        self.assertEqual(self.titles("vpn")[0], "Sieť")

    def test_diacritics_and_case_do_not_matter(self):
        self.assertEqual(self.titles("MIKROFÓN"), self.titles("mikrofon"))
        self.assertIn("Zvuk", self.titles("mikrofon"))

    def test_microphone_is_in_hardware_and_privacy_but_not_one_source_of_truth(self):
        # kap. 67: perspektívy Hardvér a Súkromie sú dve stránky, ktoré na seba odkazujú, nie dva zápisy
        found = self.titles("mikrofon")
        for expected in ("Zvuk", "Oprávnenia aplikácií", "Súkromie"):
            self.assertIn(expected, found)

    def test_a_setting_is_found_by_its_label_and_leads_to_its_page(self):
        hit = [h for h in model.search(self.index, "tlacidla") if h.key][0]
        self.assertEqual(hit.key.id, "window.buttons")
        self.assertEqual(hit.page.id, "windows")
        self.assertEqual(hit.path, "Prostredie › Okná")

    def test_all_words_must_match(self):
        self.assertEqual(self.titles("wifi zvuk"), [])
        self.assertTrue(self.titles("wifi dns"))

    def test_page_ranks_before_its_settings(self):
        hits = model.search(self.index, "pozadie")
        self.assertIsNone(hits[0].key)
        self.assertEqual(hits[0].title, "Pozadie")

    def test_empty_and_unknown_queries(self):
        self.assertEqual(model.search(self.index, ""), [])
        self.assertEqual(model.search(self.index, "   "), [])
        self.assertEqual(model.search(self.index, "xyzzyplugh"), [])

    def test_search_by_current_value(self):
        index = model.build_index(self.registry, lambda page, key: "light" if key.id == "color.scheme" else None)
        hits = model.search(index, "svetly")
        self.assertIn("color.scheme", [h.key.id for h in hits if h.key])

    def test_limit(self):
        self.assertEqual(len(model.search(self.index, "a", limit=3)), 3)


class StatusTest(unittest.TestCase):
    def setUp(self):
        self.registry = settings.Registry()

    def status(self, gid, **facts):
        return model.area_status(self.registry, gid, dict(FACTS, **facts))

    def test_areas_without_a_working_page_say_plan_not_ok(self):
        for gid in ("software", "hardware"):
            self.assertEqual(self.status(gid).state, "planned")

    def test_environment_shows_the_scheme_or_the_problem(self):
        self.assertEqual(self.status("environment").summary, "Tmavý motív")
        self.assertEqual(self.status("environment", scheme="light").summary, "Svetlý motív")
        broken = self.status("environment", problems=2)
        self.assertEqual(broken.state, "attention")
        self.assertIn("2", broken.summary)

    def test_data_follows_free_space(self):
        self.assertEqual(self.status("data").state, "ok")
        self.assertEqual(self.status("data", free=8 * 10**9).state, "attention")
        low = self.status("data", free=10**9)
        self.assertEqual(low.state, "problem")
        self.assertIn("plné", low.summary)
        self.assertEqual(self.status("data", free=None, total=None).state, "attention")

    def test_account_and_system_are_known_facts(self):
        self.assertEqual(self.status("account").summary, "Prihlásený: kava")
        self.assertIn("DEV", self.status("system").summary)

    def test_every_area_has_a_status_with_a_known_state(self):
        for gid, status in model.area_statuses(self.registry, FACTS).items():
            self.assertIn(status.state, model.STATES, gid)

    def test_state_is_never_colour_only(self):
        for state in model.STATES:
            self.assertTrue(model.state_glyph(state))
            self.assertTrue(model.state_text(state))
        self.assertEqual(len({model.state_glyph(s) for s in model.STATES}), len(model.STATES))

    def test_usage_state_thresholds(self):
        self.assertEqual(model.usage_state(50, 100), "ok")
        self.assertEqual(model.usage_state(9, 100), "attention")
        self.assertEqual(model.usage_state(1, 100), "problem")
        self.assertEqual(model.usage_state(None, 100), "attention")
        self.assertEqual(model.usage_state(5, 0), "attention")

    def test_gather_facts_never_raises_and_reports_real_values(self):
        facts = model.gather_facts(self.registry)
        self.assertTrue(facts["user"])
        self.assertIn(facts["scheme"], ("dark", "light", None))
        self.assertIsNotNone(facts["free"])


class HelpersTest(unittest.TestCase):
    def test_recent_is_unique_newest_first_and_limited(self):
        recent = []
        for page in ["a", "b", "c", "a", "d", "e", "f"]:
            recent = model.recent_add(recent, page)
        self.assertEqual(recent, ["f", "e", "d", "a", "c"])
        self.assertEqual(model.recent_parse("a,,b"), ["a", "b"])
        self.assertEqual(model.recent_parse(""), [])

    def test_results_text_uses_slovak_plural(self):
        self.assertEqual([model.results_text(n) for n in (1, 2, 4, 5, 12)],
                         ["1 výsledok", "2 výsledky", "4 výsledky", "5 výsledkov", "12 výsledkov"])

    def test_format_size(self):
        self.assertEqual(model.format_size(512), "512 B")
        self.assertEqual(model.format_size(85_400_000_000), "85,4 GB")

    def test_every_custom_view_is_known(self):
        for page in settings.Registry().pages:
            if page.view:
                self.assertIn(page.view, model.VIEWS)


if __name__ == "__main__":
    unittest.main()
