"""Wörterbuch: word-list parsing, deduplication, Wiktionary grammar rules,
search normalization, the committed data file, and (with
VIZU_WB_TEST_DB_URL = a migrated test database) search, Random 5, word state
and the idempotent import against PostgreSQL."""

import json
import os
import unittest
import uuid
from pathlib import Path

from app.scripts.woerterbuch import source, wiktionary
from app.scripts.woerterbuch.build import OUT

DATA = json.loads(Path(OUT).read_text(encoding="utf-8")) if Path(OUT).exists() else None


def fake_entry(german: str, *answers: str, levels=("A1",)):
    article, lemma, reflexive = source.split_headword(german)
    e = source.Entry(source.headword_key(german), german, article, lemma, reflexive)
    for i, (lv, ans) in enumerate(zip(levels * len(answers), answers)):
        e.rows.append(source.SourceRow(lv, i + 1, german, ans, ("x", "y")))
        if lv not in e.levels:
            e.levels.append(lv)
    return e


class TestSource(unittest.TestCase):
    def test_all_rows_read_and_repaired_rows_marked(self):
        rows = {lv: source.read_rows(lv) for lv in source.LEVELS}
        self.assertEqual([len(r) for r in rows.values()], [1000, 1000, 1000, 1500, 1100])
        repaired = [r for rs in rows.values() for r in rs if r.repaired]
        self.assertEqual(sorted((r.level, r.row_id) for r in repaired), sorted(source.REPAIRS))
        c1 = next(r for r in rows["C1"] if r.row_id == 28)
        self.assertEqual((c1.german, c1.correct), ("unter der Voraussetzung, dass", "sharti bilan"))

    def test_first_row_is_data_not_a_header(self):
        self.assertEqual(source.read_rows("A1")[0].german, "der Apfel")

    def test_distractors_are_never_translations(self):
        e = next(x for x in source.load_entries() if x.german == "berücksichtigen")
        self.assertEqual(e.translations(), ["hisobga olmoq"])
        self.assertEqual(e.rows[0].wrong, ("unutmoq", "qochmoq"))

    def test_dedup_keeps_every_source_row(self):
        entries = source.load_entries()
        self.assertEqual(sum(len(e.rows) for e in entries), 5600)
        self.assertEqual(len({e.stable_id for e in entries}), len(entries))
        freundlich = next(e for e in entries if e.german == "freundlich")
        self.assertEqual(freundlich.cefr_level, "A1")
        self.assertIn("B1", freundlich.levels)
        # most frequent answer first (12 × xushmuomala vs 6 × mehribon), the other kept
        self.assertEqual(freundlich.translations(), ["xushmuomala", "mehribon"])
        self.assertIn("translation:variants", freundlich.review_reasons())

    def test_umlaut_and_article_keep_headwords_apart(self):
        self.assertNotEqual(source.headword_key("Bar"), source.headword_key("Bär"))
        self.assertNotEqual(source.headword_key("der See"), source.headword_key("die See"))

    def test_split_headword(self):
        self.assertEqual(source.split_headword("die Entscheidung"), ("die", "Entscheidung", False))
        self.assertEqual(source.split_headword("sich erholen"), (None, "erholen", True))
        self.assertEqual(source.split_headword("die politische Legitimation hinterfragen")[0], None)

    def test_uzbek_apostrophes(self):
        self.assertEqual(source.canonical_uz("to'lamoq"), source.canonical_uz("to‘lamoq"))
        self.assertEqual(source.canonical_uz("kuch yig‘moq"), "kuch yig‘moq")
        self.assertEqual(source.canonical_uz("ma'lumot"), "ma’lumot")


class TestSearchKey(unittest.TestCase):
    def test_folding(self):
        for a, b in (("Größe", "grosse"), ("über", "ueber"), ("Ärger", "arger"), ("MÜDE", "muede"), ("o‘qimoq", "oqimoq")):
            with self.subTest(a=a):
                self.assertEqual(source.search_key(a), source.search_key(b))

    def test_query_keys_drop_article(self):
        from app.services.dictionary import query_keys

        self.assertEqual(query_keys("die Entscheidung")[0], "entscheidung")
        self.assertEqual(query_keys("sich erholen")[0], "erholen")
        self.assertEqual(query_keys("diese")[0], "diese")


class TestGrammarRules(unittest.TestCase):
    def test_head_genders(self):
        self.assertEqual(wiktionary.head_genders("Vater", "Vater m (strong, genitive Vaters, plural Väter, diminutive Väterchen n)"), ["m"])
        self.assertEqual(wiktionary.head_genders("Joghurt", "Joghurt m or n (strong)"), ["m", "n"])
        self.assertEqual(wiktionary.head_genders("Leute", "Leute pl (plural only)"), ["pl"])

    def test_compound_takes_last_part(self):
        nouns = {"Helm": ["Helm m (strong, plural Helme)", "Helme", False], "Ergebnis": ["Ergebnis n (plural Ergebnisse)", "Ergebnisse", False]}
        g, part = wiktionary.compound_noun(fake_entry("der Fahrradhelm", "velosiped shlemi"), nouns)
        self.assertEqual((g["plural"], part), ("die Fahrradhelme", "Helm"))
        g, _ = wiktionary.compound_noun(fake_entry("die Forschungsergebnisse", "natijalar"), nouns)
        self.assertEqual((g["number"], g["singular"]), ("Plural", "das Forschungsergebnis"))
        self.assertIsNone(wiktionary.compound_noun(fake_entry("die Fahrradhelm", "x"), nouns))  # gender must match

    def test_verb_forms_come_from_wiktionary(self):
        forms = [("steht auf", ["present", "singular", "third-person"]), ("stand auf", ["past"]), ("aufgestanden", ["participle", "past"]),
                 ("sein", ["auxiliary"])]
        persons = ["stehe auf", "stehst auf", "steht auf", "stehen auf", "steht auf", "stehen auf"]
        tags = [("first-person", "singular"), ("second-person", "singular"), ("third-person", "singular"),
                ("first-person", "plural"), ("second-person", "plural"), ("third-person", "plural")]
        forms += [(f, ["indicative", "present", *t]) for f, t in zip(persons, tags)]
        subset = {"aufstehen": [{"word": "aufstehen", "pos": "verb", "head": ["aufstehen (strong, …)"], "ipa": None, "glosses": [],
                                 "sense_tags": [], "forms": [{"form": f, "tags": t} for f, t in forms]}]}
        pos, g, _, src, reasons = wiktionary.resolve(fake_entry("aufstehen", "turmoq"), subset, {})
        self.assertEqual((pos, src), ("Verb", "wiktionary"))
        self.assertEqual((g["praeteritum"], g["partizip_ii"], g["perfekt"], g["separable"]), ("stand auf", "aufgestanden", "ist aufgestanden", True))
        self.assertEqual([p["form"] for p in g["praesens"]], persons)
        self.assertEqual(reasons, [])

    def test_reflexive_present_gets_pronoun_and_review(self):
        tags = [("first-person", "singular"), ("second-person", "singular"), ("third-person", "singular"),
                ("first-person", "plural"), ("second-person", "plural"), ("third-person", "plural")]
        persons = ["erhole", "erholst", "erholt", "erholen", "erholt", "erholen"]
        forms = [{"form": f, "tags": ["indicative", "present", *t]} for f, t in zip(persons, tags)]
        forms += [{"form": "erholte", "tags": ["past"]}, {"form": "erholt", "tags": ["participle", "past"]}, {"form": "haben", "tags": ["auxiliary"]}]
        subset = {"erholen": [{"word": "erholen", "pos": "verb", "head": ["erholen (weak, …)"], "ipa": None, "glosses": [], "sense_tags": [], "forms": forms}]}
        _, g, _, _, reasons = wiktionary.resolve(fake_entry("sich erholen", "dam olmoq"), subset, {})
        self.assertEqual(g["praesens"][0]["form"], "erhole mich")
        self.assertEqual(g["perfekt"], "hat sich erholt")
        self.assertIn("grammar:reflexive_pronoun_accusative_assumed", reasons)

    def test_conjunction_word_order_rule(self):
        self.assertEqual(wiktionary.conjunction_rule("weil")["type"], "subordinierend")
        self.assertEqual(wiktionary.conjunction_rule("trotzdem")["type"], "Konjunktionaladverb")
        self.assertEqual(wiktionary.conjunction_rule("und")["type"], "koordinierend")
        self.assertIsNone(wiktionary.conjunction_rule("Haus"))


@unittest.skipUnless(DATA, "dictionary.json not built")
class TestDataFile(unittest.TestCase):
    def test_counts_and_ids(self):
        entries = DATA["entries"]
        self.assertEqual(len({e["stable_id"] for e in entries}), len(entries))
        self.assertEqual(sum(len(e["sources"]) for e in entries), 5600)
        self.assertEqual(DATA["attribution"]["license"], "CC BY-SA 4.0")

    def test_statuses_never_claim_more_than_the_source(self):
        for e in DATA["entries"]:
            with self.subTest(e=e["german"]):
                self.assertIn(e["translation_status"], ("source", "needs_review"))
                self.assertIn(e["example_status"], ("needs_review", "none"))  # nothing is teacher-reviewed yet
                if e["example_de"]:
                    self.assertEqual(e["example_status"], "needs_review")
                    self.assertTrue(e["example_uz"])
                if e["grammar_source"] == "none":
                    self.assertIn(e["grammar_status"], ("none", "needs_review"))
                if e["grammar_source"] == "wiktionary_compound":
                    self.assertEqual(e["grammar_status"], "needs_review")
                self.assertNotIn(e["translation"], [d for s in e["sources"] for d in s["distractors"]] if len(e["sources"]) == 1 else [])

    def test_known_entries(self):
        by = {e["german"]: e for e in DATA["entries"]}
        self.assertEqual(by["die Entscheidung"]["grammar"]["plural"], "die Entscheidungen")
        self.assertEqual(by["berücksichtigen"]["grammar"]["perfekt"], "hat berücksichtigt")
        self.assertEqual(by["praktisch"]["grammar"]["superlativ"], "am praktischsten")

    def test_review_flags_reach_the_entries(self):
        by = {e["german"]: e for e in DATA["entries"]}
        # a wrong Uzbek answer is never shown as "source"
        self.assertEqual(by["das Betriebssystem"]["translation_status"], "needs_review")
        self.assertEqual(by["der Wolkenkratzer"]["translation_status"], "needs_review")
        # a headword that is not correct German stays hidden, but is kept
        for german in ("lärmlich", "die Sicherheitlücke", "die Zeitungskiosk", "möglich qilmoq"):
            self.assertFalse(by[german]["is_published"], german)
            self.assertTrue(any(n.startswith(("invalid_lemma:", "misspelling:", "wrong_article:")) for n in by[german]["review_notes"]))
        # an unidiomatic phrase stays visible with a note
        self.assertTrue(by["folglich betrachtet"]["is_published"])
        self.assertIn("unidiomatic:", " ".join(by["folglich betrachtet"]["review_notes"]))
        self.assertTrue(by["die Entscheidung"]["is_published"])


DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.models.user import User
        from app.scripts import import_woerterbuch

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        db = cls.Session()
        import_woerterbuch.run(db, DATA["entries"], dry_run=False)
        cls.users = []
        for _ in range(2):
            u = User(email=f"wb-{uuid.uuid4().hex[:8]}@test.local", username=f"wb_{uuid.uuid4().hex[:8]}", password_hash="x",
                     is_active=True, is_verified=True, is_superuser=False, role="STUDENT", is_banned=False, preferred_language="uz")
            db.add(u)
            cls.users.append(u)
        db.commit()
        cls.user_ids = [u.id for u in cls.users]
        db.close()

    def setUp(self):
        from app.models.user import User

        self.db = self.Session()
        self.user, self.other = (self.db.get(User, i) for i in self.user_ids)

    def tearDown(self):
        self.db.close()

    def test_import_is_idempotent(self):
        from app.scripts import import_woerterbuch

        stats = import_woerterbuch.run(self.db, DATA["entries"], dry_run=True)
        self.assertEqual((stats["create"], stats["update"], stats["unchanged"]), (0, 0, len(DATA["entries"])))

    def test_search_ranks_exact_then_prefix(self):
        from app.services import dictionary as svc

        res = svc.search(self.db, "Entscheidung")
        self.assertEqual(res["items"][0]["german"], "die Entscheidung")
        self.assertEqual(svc.search(self.db, "die entscheidung")["items"][0]["german"], "die Entscheidung")
        self.assertEqual(svc.search(self.db, "ueberzeugen")["items"][0]["lemma"][:6], "überze")

    def test_search_by_uzbek_and_filters(self):
        from app.services import dictionary as svc

        res = svc.search(self.db, "olma")
        self.assertEqual(res["items"][0]["german"], "der Apfel")
        a1 = svc.search(self.db, "e", level="A1", page_size=50)
        self.assertTrue(all("A1" in i["levels"] for i in a1["items"]))
        verbs = svc.search(self.db, "en", pos="Verb", page_size=50)
        self.assertTrue(verbs["items"] and all(i["part_of_speech"] == "Verb" for i in verbs["items"]))
        self.assertEqual(svc.search(self.db, "%")["total"], 0)  # LIKE wildcards are literal
        self.assertEqual(svc.search(self.db, "   ")["total"], 0)

    def test_random_five_distinct_unseen_first_then_refill(self):
        from app.services import dictionary as svc

        pool = svc.meta(self.db)["levels"]["B1"]
        seen = []
        for _ in range(pool // 5):
            batch = svc.random_five(self.db, self.user, "B1")
            ids = [i["id"] for i in batch["items"]]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertEqual(len(ids), 5)
            self.assertTrue(set(ids).isdisjoint(seen))  # no word twice while unseen ones remain
            self.assertTrue(all("B1" in i["levels"] for i in batch["items"]))
            seen += ids
        batch = svc.random_five(self.db, self.user, "B1")  # pool nearly exhausted: refill, still 5 distinct
        ids = [i["id"] for i in batch["items"]]
        self.assertEqual(len(set(ids)), 5)
        self.assertEqual(batch["unseen_before"], pool - len(seen))
        # another student is not affected
        self.assertEqual(svc.random_five(self.db, self.other, "B1")["unseen_before"], pool)

    def test_mark_saved_and_my_words_are_per_user(self):
        from app.services import dictionary as svc

        sid = svc.search(self.db, "Apfel")["items"][0]["id"]
        svc.set_saved(self.db, self.user, sid, True)
        card = svc.mark(self.db, self.user, sid, "unknown")
        self.assertEqual((card["me"]["saved"], card["me"]["status"]), (True, "unknown"))
        card = svc.mark(self.db, self.user, sid, "known")
        self.assertEqual(card["me"]["status"], "known")
        mine = svc.my_words(self.db, self.user, "saved")
        self.assertIn(sid, [i["id"] for i in mine["items"]])
        self.assertNotIn(sid, [i["id"] for i in svc.my_words(self.db, self.other, "saved")["items"]])
        self.assertFalse(svc.entry_card(self.db, self.other, sid)["me"]["saved"])

    def test_card_hides_audit_data(self):
        from app.services import dictionary as svc

        card = svc.entry_card(self.db, self.user, svc.search(self.db, "berücksichtigen")["items"][0]["id"])
        self.assertNotIn("sources", card)
        self.assertNotIn("review_notes", card)
        self.assertEqual(card["grammar"]["praeteritum"], "berücksichtigte")
        self.assertEqual(card["attribution"]["license"], "CC BY-SA 4.0")

    def test_flagged_headwords_are_not_served(self):
        from app.services import dictionary as svc

        self.assertEqual([i["german"] for i in svc.search(self.db, "Sicherheitlücke")["items"]], [])
        self.assertNotIn("die Sicherheitlücke", [i["german"] for i in svc.search(self.db, "Sicherheit")["items"]])
        self.assertIn("der Sicherheitsgurt", [i["german"] for i in svc.search(self.db, "Sicherheit")["items"]])


if __name__ == "__main__":
    unittest.main()
