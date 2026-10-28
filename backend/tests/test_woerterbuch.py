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
        # homonyms with other forms: the meaning decides, so a person must
        for german in ("sich bewegen", "die Bank", "die Mutter", "übersetzen"):
            self.assertEqual(by[german]["grammar_status"], "needs_review", german)

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


class TestCsvExport(unittest.TestCase):
    """docs/{A1..C1}-words.csv in the 22-column format (export_csv.py)."""

    @classmethod
    def setUpClass(cls):
        import csv

        from app.scripts.woerterbuch import export_csv

        cls.export_csv = export_csv
        cls.files = {}
        for level in source.LEVELS:
            with (export_csv.DOCS / f"{level}-words.csv").open(encoding="utf-8", newline="") as f:
                cls.files[level] = list(csv.reader(f))

    def test_same_header_original_ids_in_order(self):
        for level, rows in self.files.items():
            with self.subTest(level=level):
                self.assertEqual(tuple(rows[0]), self.export_csv.COLUMNS)
                self.assertTrue(all(len(r) == 22 for r in rows))
                ids = [int(r[0]) for r in rows[1:]]
                # repeats were merged, so ids are the originals' ids with gaps, still in order
                self.assertEqual(ids, sorted(ids))
                self.assertTrue(set(ids) <= {r.row_id for r in source.read_rows(level)})
                self.assertTrue(all(r[1] == level for r in rows[1:]))

    def test_grammar_columns_only_for_their_word_type(self):
        col = {c: i for i, c in enumerate(self.export_csv.COLUMNS)}
        verb = [c for c in self.export_csv.COLUMNS if c.startswith(("verb_", "presens_"))]
        for rows in self.files.values():
            for r in rows[1:]:
                with self.subTest(row=r[:3]):
                    if r[col["word_type"]] != "Nomen":
                        self.assertEqual(r[col["article"]] + r[col["plural"]], "")
                    if r[col["word_type"]] != "Verb":
                        self.assertEqual("".join(r[col[c]] for c in verb), "")
                    if r[col["word_type"]] != "Adjektiv":
                        self.assertEqual(r[col["adjective_komparativ"]] + r[col["adjective_superlativ"]], "")
                    self.assertIn(r[col["status"]], ("verified", "needs_review"))
                    self.assertFalse({"NULL", "None", "N/A"} & set(r))

    def test_verified_rows_are_complete_and_open_rows_say_why(self):
        from app.scripts.woerterbuch import docs_csv

        loaded = docs_csv.load()
        for r in loaded.rows:
            with self.subTest(row=r.key):
                if r.values["status"] == "verified":
                    self.assertTrue(r.values["translation"] and r.values["example_de"] and r.values["example_uz"] and r.values["audio_text"])
                else:
                    self.assertTrue(r.review and r.review["reasons"])

    def test_docs_validate_link_and_hold_no_repeats(self):
        from collections import Counter

        from app.scripts.woerterbuch import docs_csv

        loaded = docs_csv.load()
        self.assertEqual((loaded.errors, loaded.warnings), ([], []))
        self.assertTrue(all(r.extra.get("quiz_distractors") for r in loaded.rows))
        repeats = Counter((r.level, r.group_key) for r in loaded.rows)
        self.assertEqual([k for k, n in repeats.items() if n > 1], [])
        self.assertFalse(any(r.hidden for r in loaded.rows))

    def test_review_is_applied_and_reapplying_changes_nothing(self):
        import tempfile, shutil

        from app.scripts.woerterbuch import apply_review

        rows = {(r[1], r[2]): dict(zip(self.export_csv.COLUMNS, r)) for rows in self.files.values() for r in rows[1:]}
        apfel = rows[("A1", "Apfel")]
        self.assertEqual((apfel["article"], apfel["plural"], apfel["audio_text"]), ("der", "Äpfel", "der Apfel"))
        anrufen = rows[("A1", "anrufen")]
        self.assertEqual((anrufen["verb_praeteritum"], anrufen["verb_auxiliary"], anrufen["presens_du"]), ("rief an", "haben", "rufst an"))
        self.assertEqual(rows[("A2", "lärmend")]["audio_text"], "lärmend")  # was „lärmlich“
        self.assertEqual(rows[("B2", "Sicherheitslücke")]["plural"], "Sicherheitslücken")
        self.assertEqual(rows[("B2", "sich bewegen")]["verb_praeteritum"], "bewegte")
        self.assertEqual(rows[("B2", "sich merken")]["presens_ich"], "merke mir")
        self.assertEqual(rows[("B2", "während")]["word_type"], "Konjunktion")
        self.assertEqual(rows[("A1", "hilfsbereit")]["translation"], "yordamga tayyor")
        self.assertNotIn(("A2", "Krankenhausticket"), rows)
        with tempfile.TemporaryDirectory() as tmp:
            for p in self.export_csv.DOCS.glob("*.csv"):
                shutil.copy(p, tmp)
            stats = apply_review.apply(Path(tmp), dry_run=True, allow_unused=True)
        self.assertEqual((stats["changes_logged"], stats["rows_merged"], stats["rows_deleted"]), (0, 0, 0))


DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestDatabase(unittest.TestCase):
    """docs/ CSVs -> import -> search, card, Random 5, saved words (PostgreSQL)."""

    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.models.user import User
        from app.scripts import import_woerterbuch

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        db = cls.Session()
        import_woerterbuch.run(db, prune_missing=True)
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

    def _count(self, *where):
        from sqlalchemy import func, select

        from app.models.dictionary import DictionaryEntry

        return self.db.scalar(select(func.count()).select_from(DictionaryEntry).where(*where))

    def test_every_csv_row_imported_with_its_id_level_and_extra_data(self):
        from sqlalchemy import select

        from app.models.dictionary import DictionaryEntry as E
        from app.scripts import import_woerterbuch

        from app.scripts.woerterbuch import docs_csv

        loaded = docs_csv.load()
        expected = {lv: sum(r.level == lv for r in loaded.rows) for lv in source.LEVELS}
        self.assertEqual({lv: self._count(E.level == lv) for lv in source.LEVELS}, expected)
        apfel = self.db.scalar(select(E).where(E.level == "A1", E.source_id == 1))
        self.assertEqual((apfel.lemma, apfel.article, apfel.plural, apfel.translation), ("Apfel", "der", "Äpfel", "olma"))
        self.assertEqual(len(apfel.extra["quiz_distractors"]), 2)
        # the CSV status is taken as it is
        self.assertEqual(self._count(E.status == "verified"), sum(r.values["status"] == "verified" for r in loaded.rows))
        self.assertEqual(self._count(E.is_primary.is_(False)), 0)
        stats = import_woerterbuch.run(self.db, dry_run=True)
        self.assertEqual(sum(s.get("unchanged", 0) for s in stats["levels"].values()), len(loaded.rows))
        self.assertEqual(sum(s.get("created", 0) + s.get("updated", 0) for s in stats["levels"].values()), 0)

    def test_prune_moves_saved_words_to_the_kept_row(self):
        import shutil
        import tempfile

        from sqlalchemy import select

        from app.models.dictionary import DictionaryEntry as E, DictionaryUserWord as W
        from app.scripts import import_woerterbuch

        apfel = self.db.scalar(select(E).where(E.level == "A1", E.source_id == 1))
        from sqlalchemy import inspect

        gone = E(**{a.key: getattr(apfel, a.key) for a in inspect(E).column_attrs if a.key not in ("id", "created_at", "updated_at")})
        gone.source_id, gone.content_hash = 99999, "x"
        self.db.add(gone)
        self.db.flush()
        self.db.add(W(user_id=self.other.id, entry_id=gone.id, saved=True, seen_count=2))
        self.db.commit()
        with tempfile.TemporaryDirectory() as tmp:
            for p in import_woerterbuch.docs_csv.DOCS_DIR.glob("*.csv"):
                shutil.copy(p, tmp)
            with (Path(tmp) / "worterbuch-merges.csv").open("a", encoding="utf-8", newline="") as f:
                f.write("A1,99999,A1,1,der Apfel\r\n")
            stats = import_woerterbuch.run(self.db, Path(tmp), prune_missing=True)
        self.assertEqual((stats["pruned"], stats["moved_user_words"]), (1, 1))
        self.assertIsNone(self.db.scalar(select(E).where(E.level == "A1", E.source_id == 99999)))
        moved = self.db.scalar(select(W).where(W.user_id == self.other.id, W.entry_id == apfel.id))
        self.assertTrue(moved.saved)
        self.db.delete(moved)
        self.db.commit()

    def test_search_prefix_first_then_contains(self):
        from app.services import dictionary as svc

        res = svc.search(self.db, self.user, "Haus", page_size=20)
        lemmas = [i["lemma"] for i in res["items"]]
        self.assertEqual(lemmas[0], "Haus")
        starts = [source.search_key(x).startswith("haus") for x in lemmas]
        self.assertEqual(starts, sorted(starts, reverse=True))  # every prefix match before any other match
        self.assertGreater(sum(starts), 1)
        self.assertEqual(svc.search(self.db, self.user, "haus")["items"][0]["lemma"], "Haus")

    def test_search_uzbek_umlauts_forms_and_filters(self):
        from app.services import dictionary as svc

        top = lambda q, **kw: [i["lemma"] for i in svc.search(self.db, self.user, q, **kw)["items"]]  # noqa: E731
        self.assertIn("Haus", top("uy")[:3])
        self.assertEqual(top("Äpfel")[0], "Apfel")  # plural form
        self.assertEqual(top("aepfel")[0], "Apfel")
        self.assertEqual(top("Strasse"), top("Straße"))
        self.assertIn("laufen", top("läuft"))  # Präsens form
        self.assertTrue(all(i["level"] == "B2" for i in svc.search(self.db, self.user, "e", level="B2", page_size=50)["items"]))
        verbs = svc.search(self.db, self.user, "en", word_type="Verb", page_size=50)["items"]
        self.assertTrue(verbs and all(i["word_type"] == "Verb" for i in verbs))
        self.assertEqual(svc.search(self.db, self.user, "%")["total"], 0)  # LIKE wildcards are literal
        self.assertEqual(svc.search(self.db, self.user, "  ")["total"], 0)
        # a repeated row is offered once per level
        items = svc.search(self.db, self.user, "zuverlässig", page_size=50)["items"]
        pairs = [(i["level"], i["lemma"]) for i in items]
        self.assertEqual(len(pairs), len(set(pairs)))

    def test_card_by_word_type_and_hidden_rows(self):
        from fastapi import HTTPException
        from sqlalchemy import select

        from app.models.dictionary import DictionaryEntry as E
        from app.services import dictionary as svc

        anrufen = svc.search(self.db, self.user, "anrufen")["items"][0]
        card = svc.entry_card(self.db, self.user, anrufen["id"])
        self.assertEqual((card["verb"]["praeteritum"], card["verb"]["auxiliary"]), ("rief an", "haben"))
        self.assertEqual([p["person"] for p in card["verb"]["praesens"]], ["ich", "du", "er/sie/es", "wir", "ihr", "sie/Sie"])
        self.assertIsNone(card["adjective"])
        self.assertNotIn("quiz_distractors", card["details"])
        self.assertNotIn("review", card)
        self.assertEqual(card["status"], "verified")
        self.assertEqual(card["attribution"]["license"], "CC BY-SA 4.0")
        zuv = svc.entry_card(self.db, self.user, svc.search(self.db, self.user, "zuverlässig", level="A2")["items"][0]["id"])
        self.assertEqual(zuv["adjective"]["komparativ"], "zuverlässiger")
        self.assertIn("B1", zuv["also_in"])
        self.assertEqual(self.db.scalar(select(E).where(E.is_published.is_(False)).limit(1)), None)
        self.assertEqual(svc.search(self.db, self.user, "Sicherheitslücke")["items"][0]["lemma"], "Sicherheitslücke")
        with self.assertRaises(HTTPException):
            svc.entry_card(self.db, self.user, "X9-1")

    def test_random_five_distinct_mixed_levels_and_fresh(self):
        from app.services import dictionary as svc

        previous: set[str] = set()
        for _ in range(8):
            draw = svc.random_five(self.db, self.user)
            ids = [i["id"] for i in draw["items"]]
            self.assertEqual(len(ids), 5)
            self.assertEqual(len(set(ids)), 5)
            self.assertEqual(len({source.search_key(i["lemma"]) for i in draw["items"]}), 5)  # never the same German word twice
            self.assertEqual(sorted(i["level"] for i in draw["items"]), list(source.LEVELS))  # one per level
            self.assertTrue(previous.isdisjoint(ids))  # "Yana 5 ta": just-seen words do not come back
            previous = set(ids)
        b1 = svc.random_five(self.db, self.user, "B1")
        self.assertTrue(all(i["level"] == "B1" for i in b1["items"]))
        self.assertEqual(len({i["id"] for i in b1["items"]}), 5)

    def test_star_is_per_user_idempotent_and_in_sync(self):
        from sqlalchemy import func, select

        from app.models.dictionary import DictionaryUserWord as W
        from app.services import dictionary as svc

        word = svc.search(self.db, self.user, "Apfel")["items"][0]
        for _ in range(2):  # saving twice keeps one row
            svc.set_saved(self.db, self.user, word["id"], True)
        rows = self.db.scalar(select(func.count()).select_from(W).where(W.user_id == self.user.id, W.saved.is_(True)))
        self.assertEqual(rows, 1)
        self.assertTrue(svc.search(self.db, self.user, "Apfel")["items"][0]["saved"])
        self.assertTrue(svc.entry_card(self.db, self.user, word["id"])["saved"])
        mine = svc.saved_words(self.db, self.user)
        self.assertEqual([i["id"] for i in mine["items"]], [word["id"]])
        self.assertEqual(mine["by_level"]["A1"], 1)
        self.assertEqual(svc.saved_words(self.db, self.user, q="olma")["total"], 1)
        self.assertEqual(svc.saved_words(self.db, self.user, level="C1")["total"], 0)
        # another student sees nothing of it
        self.assertEqual(svc.saved_words(self.db, self.other)["total"], 0)
        self.assertFalse(svc.search(self.db, self.other, "Apfel")["items"][0]["saved"])
        svc.set_saved(self.db, self.user, word["id"], False)
        self.assertEqual(svc.saved_words(self.db, self.user)["total"], 0)
        self.assertFalse(svc.entry_card(self.db, self.user, word["id"])["saved"])


class TestApi(unittest.TestCase):
    def test_every_dictionary_route_requires_a_logged_in_user(self):
        from app.api.dependencies.auth import get_current_user
        from app.api.dictionary.router import router

        for route in router.routes:
            with self.subTest(route=route.path):
                self.assertIn(get_current_user, [d.call for d in route.dependant.dependencies])

    def test_import_rejects_broken_files_without_writing(self):
        import shutil
        import tempfile

        from app.scripts import import_woerterbuch
        from app.scripts.woerterbuch import docs_csv

        with tempfile.TemporaryDirectory() as tmp:
            for p in docs_csv.DOCS_DIR.glob("*.csv"):
                shutil.copy(p, tmp)
            a1 = Path(tmp) / "A1-words.csv"
            lines = a1.read_text(encoding="utf-8").splitlines()
            lines[3] = lines[2]  # duplicate id
            lines[4] = lines[4].rsplit(",", 1)[0] + ",checked"  # unknown status
            a1.write_text("\n".join(lines), encoding="utf-8")

            class NoDb:
                def scalars(self, *_):
                    raise AssertionError("the database must not be touched")

            with self.assertRaises(import_woerterbuch.ImportRejected) as ctx:
                import_woerterbuch.run(NoDb(), Path(tmp))
            text = " ".join(ctx.exception.errors)
            self.assertIn("duplicate id", text)
            self.assertIn("status", text)


if __name__ == "__main__":
    unittest.main()
