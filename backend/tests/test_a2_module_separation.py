"""A2 module separation (docs/a2-module-separation-report.md): Wortschatz
dictionary + tests, Schreiben analysis + history, Lesen / Wortschatz /
Grammatik written tasks outside Schreiben.

Pure parts run everywhere; the DB / HTTP parts need VIZU_WB_TEST_DB_URL (a
migrated test database) and httpx for the TestClient."""

import asyncio
import importlib.util
import os
import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
HAS_HTTPX = importlib.util.find_spec("httpx") is not None


def word(german, translation, article=None, plural=None, word_type=None, prt=None, p2=None, aux=None, example=None, example_uz=None):
    return {"german_word": german, "translation": translation, "article": article, "plural": plural, "word_type": word_type,
            "verb_praeteritum": prt, "verb_partizip_ii": p2, "verb_auxiliary": aux, "example_sentence": example, "example_translation": example_uz}


NOUNS = [
    word("Bewerbung", "ariza", "die", "Bewerbungen", "Nomen", example="Ich schicke meine Bewerbung per E-Mail.", example_uz="Arizamni yuboraman."),
    word("Unternehmen", "korxona", "das", "Unternehmen", "Nomen", example="Das Unternehmen ist groß.", example_uz="Korxona katta."),
    word("Erfahrung", "tajriba", "die", "Erfahrungen", "Nomen", example="Sie hat viel Erfahrung.", example_uz="Uning tajribasi ko'p."),
    word("Projekt", "loyiha", "das", "Projekte", "Nomen", example="Das Projekt ist fertig.", example_uz="Loyiha tayyor."),
    word("Kollege", "hamkasb", "der", "Kollegen", "Nomen", example="Mein Kollege hilft mir.", example_uz="Hamkasbim yordam beradi."),
    word("Gehalt", "maosh", "das", "Gehälter", "Nomen", example="Das Gehalt ist gut.", example_uz="Maosh yaxshi."),
    word("Chef", "boshliq", "der", None, "Nomen"),
]
VERBS = [
    word("arbeiten", "ishlamoq", word_type="Verb", prt="arbeitete", p2="gearbeitet", aux="haben", example="Wir arbeiten zusammen.", example_uz="Biz birga ishlaymiz."),
    word("fahren", "bormoq", word_type="Verb", prt="fuhr", p2="gefahren", aux="sein"),
    word("lernen", "o'rganmoq", word_type="Verb", prt="lernte", p2="gelernt", aux="haben"),
    word("bewerben", "ariza bermoq", word_type="Verb"),  # no forms -> never in the verb test
]


# ============================================================
# Wortschatz tests (pure)
# ============================================================


class TestWortschatzTestBuilder(unittest.TestCase):
    def setUp(self):
        from app.services.lesson_skills import wortschatz_tests as wt

        self.wt = wt
        self.sets = {s["key"]: s for s in wt.build_sets(NOUNS + VERBS)}

    def _validated(self, s):
        from app.services.lesson_skills import admin as skill_admin

        return skill_admin.validate_questions(s["questions"])  # the editor's own validation must accept every question

    def test_all_seven_types_are_built_from_the_words(self):
        self.assertEqual(list(self.sets), list(self.wt.ORDER))
        for s in self.sets.values():
            self.assertEqual(s["source"], "vizu")
            self.assertLessEqual(len(s["questions"]), self.wt.MAX_QUESTIONS)
            self._validated(s)

    def test_multiple_choice_has_exactly_one_correct_and_distinct_options(self):
        for key in ("bedeutung", "uebersetzung", "artikel"):
            for q in self.sets[key]["questions"]:
                texts = [o["text"].casefold() for o in q["options"]]
                self.assertEqual(len(texts), len(set(texts)), q)
                self.assertEqual(sum(o["is_correct"] for o in q["options"]), 1, q)

    def test_keys_come_from_the_word_data(self):
        artikel = {q["question"]: next(o["text"] for o in q["options"] if o["is_correct"]) for q in self.sets["artikel"]["questions"]}
        self.assertEqual(artikel["___ Bewerbung"], "die")
        self.assertEqual(artikel["___ Unternehmen"], "das")
        plural = {q["question"]: q["config"]["accepted"] for q in self.sets["plural"]["questions"]}
        self.assertIn("Gehälter", plural["das Gehalt → die ___"])
        self.assertNotIn("der Chef → die ___", plural)  # no plural stored -> not asked
        verbs = {q["question"].split(" — ")[0]: q["config"]["gaps"] for q in self.sets["verbformen"]["questions"]}
        self.assertEqual(verbs["fahren"]["aux"]["accepted"], ["ist"])
        self.assertEqual(verbs["arbeiten"]["p2"]["accepted"], ["gearbeitet"])
        self.assertNotIn("bewerben", verbs)  # forms missing -> never invented

    def test_no_repetition_inside_a_set_and_meaning_types_split_the_words(self):
        for s in self.sets.values():
            keys = [(q["question"], (q.get("config") or {}).get("text")) for q in s["questions"]]
            self.assertEqual(len(keys), len(set(keys)), s["key"])
        asked_b = {q["question"].split("“")[0].strip("„ ") for q in self.sets["bedeutung"]["questions"]}
        asked_u = {next(o["text"] for o in q["options"] if o["is_correct"]) for q in self.sets["uebersetzung"]["questions"]}
        self.assertFalse(asked_b & asked_u)

    def test_ambiguous_translation_is_not_asked(self):
        words = NOUNS + [word("Firma", "korxona", "die", "Firmen", "Nomen")]  # same translation as Unternehmen
        sets = {s["key"]: s for s in self.wt.build_sets(words)}
        asked = " ".join(q["question"] for k in ("bedeutung", "uebersetzung") for q in sets.get(k, {"questions": []})["questions"])
        self.assertNotIn("Firma", asked)
        self.assertNotIn("„korxona“", asked)

    def test_gap_sentence_uses_the_word_as_written_and_the_translation_hint(self):
        gap = self.wt._sentence_gap(NOUNS[0])
        self.assertEqual(gap, ("Ich schicke meine [[w]] per E-Mail.", "Bewerbung"))
        self.assertIsNone(self.wt._sentence_gap(word("Haus", "uy", "das", example="Die Häuser sind alt.", example_uz="x")))  # no exact form
        for key in ("luecke", "kontext"):
            for q in self.sets.get(key, {"questions": []})["questions"]:
                self.assertTrue(q["question"].startswith("("))

    def test_plural_only_nouns_are_not_asked_for_gender_or_plural(self):
        words = NOUNS + [word("Medien", "Zeitungen, Internet", "die", "Medien", "Nomen")]
        sets = {s["key"]: s for s in self.wt.build_sets(words)}
        asked = " ".join(q["question"] for k in ("artikel", "plural") for q in sets[k]["questions"])
        self.assertNotIn("Medien", asked)

    def test_too_few_questions_leave_a_type_out(self):
        sets = {s["key"] for s in self.wt.build_sets(NOUNS[:2])}
        self.assertNotIn("bedeutung", sets)


# ============================================================
# Enrichment + missing fields (pure)
# ============================================================


class TestWortschatzEnrichment(unittest.TestCase):
    def _entry(self, **kw):
        base = dict(level="A2", source_id=7, word_type="Nomen", plural="Bewerbungen", verb_praeteritum=None, verb_partizip_ii=None,
                    verb_auxiliary=None, example_de="Ich schreibe eine Bewerbung.", example_uz="Ariza yozaman.")
        base.update(kw)
        return SimpleNamespace(word_id=f"{base['level']}-{base['source_id']}", **base)

    def _vocab(self, **kw):
        base = dict(german_word="Bewerbung", article="die", plural=None, translation="ariza", word_type=None, verb_praeteritum=None,
                    verb_partizip_ii=None, verb_auxiliary=None, example_sentence=None, example_translation=None)
        base.update(kw)
        return SimpleNamespace(**base)

    def test_fills_only_empty_fields_with_the_entry_as_source(self):
        from app.services.lesson_skills import wortschatz

        fill = wortschatz.enrichment(self._vocab(plural="Bewerbungen (Buch)"), self._entry())
        self.assertNotIn("plural", fill)  # the book's value is never overwritten
        self.assertEqual(fill["word_type"], ("Nomen", "woerterbuch:A2-7"))
        self.assertEqual(fill["example_sentence"][0], "Ich schreibe eine Bewerbung.")

    def test_verb_fields_only_for_verbs_and_article_means_noun(self):
        from app.services.lesson_skills import wortschatz

        fill = wortschatz.enrichment(self._vocab(), self._entry(verb_praeteritum="x"))
        self.assertNotIn("verb_praeteritum", fill)
        self.assertEqual(wortschatz.enrichment(self._vocab(), None), {"word_type": ("Nomen", "book:article")})
        self.assertEqual(wortschatz.enrichment(self._vocab(article=None, german_word="genug"), None), {})  # nothing guessed

    def test_missing_fields_tell_the_admin_what_to_fill(self):
        from app.services.lesson_skills import wortschatz

        self.assertEqual(wortschatz.missing_fields(self._vocab(word_type="Nomen")), ["plural", "example_sentence"])
        verb = self._vocab(article=None, german_word="fahren", word_type="Verb", verb_praeteritum="fuhr", example_sentence="Ich fahre.",
                           example_translation="Men boraman.")
        self.assertEqual(wortschatz.missing_fields(verb), ["verb_partizip_ii", "verb_auxiliary"])
        self.assertEqual(wortschatz.missing_fields(self._vocab(article=None))[0], "word_type")


# ============================================================
# Schreiben analysis (pure)
# ============================================================


class TestSchreibenAnalysis(unittest.TestCase):
    TEXT = "Ich habe gestern ins Kino gegangen. Der Film war sehr gut und ich mag es."

    def test_a2_rubric_has_the_seven_criteria(self):
        from app.services.lesson_skills import levels

        rubric = levels.writing_rubric("A2")
        self.assertEqual([c["key"] for c in rubric], ["task", "grammar", "vocabulary", "sentence", "spelling", "coherence", "structure"])
        self.assertEqual(sum(c["max"] for c in rubric), 100)
        self.assertTrue(rubric[0]["name"].startswith("Aufgabenbewältigung"))
        self.assertIn("B1/B2/C1 talablarini qo'llama", levels.WRITING_EXPECTATIONS["A2"])
        for comp, r in levels.COMPETENCY_RUBRICS.items():
            self.assertEqual(sum(c["max"] for c in r), 100, comp)
        self.assertEqual(levels.competency_rubric("WORTSCHATZ", "A2")[0]["key"], "meaning")
        self.assertEqual(levels.competency_rubric(None, "A2"), rubric)

    def test_result_has_errors_per_criterion_tips_weaknesses_improved_text(self):
        from app.services.lesson_skills import ai_evaluation as ai
        from app.services.lesson_skills import levels

        rubric = levels.writing_rubric("A2")
        raw = {
            "criteria": [{"key": c["key"], "score": c["max"] - 2, "comment": "ok", "tip": f"tip {c['key']}"} for c in rubric],
            "strengths": ["Gute Idee"], "weaknesses": ["Perfekt mit sein"],
            "errors": [
                {"original": "habe gestern ins Kino gegangen", "correction": "bin gestern ins Kino gegangen", "explanation": "sein", "criterion": "grammar"},
                {"original": "ich mag es", "correction": "er hat mir gefallen", "explanation": "x", "criterion": "nonsense"},
                {"original": "nicht im Text", "correction": "y", "explanation": "invented", "criterion": "grammar"},
            ],
            "improved_text": "Ich bin gestern ins Kino gegangen.", "next_practice": "Perfekt mit sein üben", "recommendation": "r", "summary": "s",
        }
        result = ai.validate_result(raw, rubric, self.TEXT, {c["key"] for c in rubric})
        self.assertEqual(result["points"], 100 - 2 * 7)
        self.assertEqual(result["criteria"][1]["tip"], "tip grammar")
        self.assertEqual([e["criterion"] for e in result["errors"]], ["grammar", None])  # unknown criterion dropped, invented error removed
        self.assertEqual(result["weaknesses"], ["Perfekt mit sein"])
        self.assertEqual(result["improved_text"], "Ich bin gestern ins Kino gegangen.")
        self.assertEqual(result["next_practice"], "Perfekt mit sein üben")

    def test_prompts_keep_competencies_apart(self):
        from app.services.lesson_skills import ai_evaluation as ai
        from app.services.lesson_skills import levels

        task = SimpleNamespace(title="T", instruction="I", feedback_language="uz", ai_instructions=None, helper_words=None, text_type="email",
                               audience=None, min_words=None, max_words=None, competency=None)
        schreiben = ai.writing_prompt(task, "x", levels.writing_rubric("A2"), "A2")
        self.assertIn("(Schreiben) tahlil", schreiben)
        self.assertIn('"improved_text"', schreiben)
        task.competency = "WORTSCHATZ"
        wortschatz = ai.writing_prompt(task, "x", levels.competency_rubric("WORTSCHATZ", "A2"), "A2")
        self.assertIn("Schreiben (yozma ish) EMAS", wortschatz)
        self.assertNotIn("Textstruktur", wortschatz)
        self.assertNotIn("Matn turi", wortschatz)
        task.competency = "LESEN"
        lesen = ai.writing_prompt(task, "x", levels.competency_rubric("LESEN", "A2"), "A2", "Die Deutschen essen gern Brot.")
        self.assertIn("O'QISH MATNI", lesen)
        self.assertIn("Die Deutschen essen gern Brot.", lesen)


class TestA2BookEditionCompetencies(unittest.TestCase):
    def test_fifteen_written_tasks_leave_schreiben(self):
        from app.scripts.vizu_deutsch_a2_buch import items

        counts, schreiben_titles = {}, []
        for n in range(1, 14):
            for item in items(n):
                if item["skill"] != "schreiben":
                    continue
                comp = item.get("competency") or "SCHREIBEN"
                counts[comp] = counts.get(comp, 0) + 1
                if comp == "SCHREIBEN":
                    schreiben_titles.append(item["title"])
        self.assertEqual(counts, {"SCHREIBEN": 25, "GRAMMATIK": 5, "WORTSCHATZ": 9, "LESEN": 1})
        for title in schreiben_titles:
            self.assertTrue(title.startswith("Schreiben"), title)


class TestWordCsvPure(unittest.TestCase):
    def test_formula_cells_are_neutralised_and_restored(self):
        from app.services.lesson_skills import word_csv

        self.assertEqual(word_csv._cell("=HYPERLINK(1)"), "'=HYPERLINK(1)")
        self.assertEqual(word_csv._uncell("'=HYPERLINK(1)"), "=HYPERLINK(1)")
        self.assertEqual(word_csv._uncell("'s Haus"), "'s Haus")

    def test_upload_checks(self):
        from fastapi import HTTPException
        from starlette.datastructures import Headers, UploadFile
        from io import BytesIO

        from app.services.lesson_skills import word_csv

        def up(name, data, mime="text/csv"):
            return UploadFile(BytesIO(data), filename=name, headers=Headers({"content-type": mime}))

        with self.assertRaises(HTTPException):
            asyncio.run(word_csv.read_upload(up("words.xlsx", b"a,b")))
        with self.assertRaises(HTTPException):
            asyncio.run(word_csv.read_upload(up("words.csv", b"a\x00b")))
        with self.assertRaises(HTTPException):
            asyncio.run(word_csv.read_upload(up("words.csv", b"x" * (word_csv.MAX_BYTES + 1))))
        self.assertEqual(asyncio.run(word_csv.read_upload(up("words.csv", b"german_word,translation\n"))), b"german_word,translation\n")


# ============================================================
# Database + HTTP
# ============================================================


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestA2ModuleSeparationDB(unittest.TestCase):
    PREFIX = "test-a2ms-"

    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker

        from app.models.language import Language
        from app.models.user import User
        from app.services.lms import structure

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        db = cls.Session()
        if db.scalar(select(Language).where(Language.code == "de")) is None:
            db.add(Language(code="de", locale="de-DE", name="Deutsch"))
            db.commit()
        structure.ensure_structure(db, "A2")
        tag = uuid.uuid4().hex[:6]
        users = {}
        for name, role in (("super", "SUPER_ADMIN"), ("editor", "CONTENT_MANAGER"), ("support", "SUPPORT"), ("student", "STUDENT"), ("other", "STUDENT")):
            users[name] = User(email=f"a2ms-{name}-{tag}@test.local", username=f"a2ms_{name}_{tag}", password_hash="x", is_active=True,
                               is_verified=True, is_superuser=False, role=role, is_banned=False, preferred_language="uz", first_name=name)
            db.add(users[name])
        db.commit()
        cls.ids = {k: v.id for k, v in users.items()}
        db.close()

    def setUp(self):
        from sqlalchemy import or_, select

        from app.models.lesson_skill import SkillExercise
        from app.models.dictionary import DictionaryEntry
        from app.models.user import User
        from app.models.vocabulary import Vocabulary
        from app.models.writing import Writing
        from app.services.a2_audio import assets

        self.db = self.Session()
        self.lessons = {lesson.number: lesson for lesson in assets.a2_lessons(self.db)}
        a2 = [lsn.id for lsn in self.lessons.values()]
        for model in (Writing, SkillExercise):
            for row in self.db.scalars(select(model).where(model.lesson_id.in_(a2))):
                self.db.delete(row)
        for row in self.db.scalars(select(Vocabulary).where(Vocabulary.lesson_id.in_(a2))):
            self.db.delete(row)
        for row in self.db.scalars(select(DictionaryEntry).where(or_(DictionaryEntry.lemma.like("Testwort%"), DictionaryEntry.lemma == "testarbeiten"))):
            self.db.delete(row)
        for lsn in self.lessons.values():
            lsn.is_published = lsn.number in (1, 2)
        self.db.commit()
        self.user = {k: self.db.get(User, v) for k, v in self.ids.items()}
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        self.tmp.cleanup()

    # ---------- helpers ----------

    def _writing(self, lesson, title, competency=None, content_id=None, ai=False, rubric=None):
        from app.models.writing import Writing

        w = Writing(lesson_id=lesson.id, title=title, instruction="Schreib etwas.", min_words=None, max_words=None, is_published=True,
                    ai_evaluation_enabled=ai, competency=competency, content_id=content_id or f"{self.PREFIX}{uuid.uuid4().hex[:8]}",
                    rubric=rubric, order_index=1)
        self.db.add(w)
        self.db.commit()
        return w

    def _word(self, lesson, german, translation, article=None, published=True, **kw):
        from app.models.vocabulary import Vocabulary

        v = Vocabulary(lesson_id=lesson.id, german_word=german, translation=translation, article=article, is_published=published,
                       order_index=kw.pop("order_index", 1), **kw)
        self.db.add(v)
        self.db.commit()
        return v

    def _client(self, who):
        from fastapi.testclient import TestClient

        from app.api.dependencies.auth import get_current_user
        from app.db.session import get_db
        from app.main import app

        app.dependency_overrides[get_db] = lambda: self.db
        if who:
            app.dependency_overrides[get_current_user] = lambda: self.user[who]
        else:
            app.dependency_overrides.pop(get_current_user, None)
        self.addCleanup(app.dependency_overrides.clear)
        return TestClient(app)

    # ---------- module separation ----------

    def test_results_count_written_tasks_only_in_their_own_competency(self):
        from app.services.lesson_skills.results import lesson_skill_results

        lesson = self.lessons[1]
        s = self._writing(lesson, "Schreiben: E-Mail")
        w = self._writing(lesson, "Wortschatz-Aufgabe", "WORTSCHATZ")
        r = self._writing(lesson, "Lesen: Fragen zum Text", "LESEN")
        g = self._writing(lesson, "Grammatik-Aufgabe", "GRAMMATIK")
        skills = lesson_skill_results(self.db, self.user["student"].id, lesson.id)["skills"]
        self.assertEqual([t["id"] for t in skills["schreiben"]["tasks"]], [s.id])
        self.assertEqual([t["id"] for t in skills["wortschatz"]["tasks"]], [w.id])
        self.assertEqual([t["id"] for t in skills["lesen"]["tasks"]], [r.id])
        self.assertEqual([t["id"] for t in skills["grammatik"]["tasks"]], [g.id])

    def test_competency_page_progress_follows_the_task(self):
        from app.services.lms import progress

        lesson = self.lessons[1]
        self._writing(lesson, "Wortschatz-Aufgabe", "WORTSCHATZ")
        state = progress.compute(self.db, self.user["student"], lesson)
        comps = {c["kind"]: c for c in state["competencies"]}
        self.assertTrue(comps["WORTSCHATZ"]["tracked"])
        self.assertEqual(comps["SCHREIBEN"]["progress_status"], progress.STATUS_NOT_AVAILABLE)

    @unittest.skipUnless(HAS_HTTPX, "HTTP part needs httpx")
    def test_student_lists_only_the_written_tasks_of_the_requested_competency(self):
        lesson = self.lessons[1]
        s = self._writing(lesson, "Schreiben: E-Mail")
        explicit = self._writing(lesson, "Schreiben: SMS", "SCHREIBEN")
        w = self._writing(lesson, "Wortschatz-Aufgabe", "WORTSCHATZ")
        r = self._writing(lesson, "Lesen: Fragen zum Text", "LESEN")
        client = self._client("student")
        default = {x["id"] for x in client.get(f"/api/v1/writings/lesson/{lesson.id}").json()}
        self.assertEqual(default, {str(s.id), str(explicit.id)})  # no Lesen / Wortschatz task in Schreiben
        self.assertEqual([x["id"] for x in client.get(f"/api/v1/writings/lesson/{lesson.id}?competency=WORTSCHATZ").json()], [str(w.id)])
        self.assertEqual([x["id"] for x in client.get(f"/api/v1/writings/lesson/{lesson.id}?competency=LESEN").json()], [str(r.id)])
        self.assertEqual(client.get(f"/api/v1/writings/lesson/{lesson.id}?competency=HOEREN").status_code, 422)

    @unittest.skipUnless(HAS_HTTPX, "HTTP part needs httpx")
    def test_only_content_editors_create_or_change_writing_tasks(self):
        lesson = self.lessons[1]
        body = {"lesson_id": str(lesson.id), "title": "Wortschatz-Aufgabe", "instruction": "x", "competency": "WORTSCHATZ"}
        self.assertEqual(self._client("support").post("/api/v1/writings", json=body).status_code, 403)
        self.assertEqual(self._client("student").post("/api/v1/writings", json=body).status_code, 403)
        created = self._client("editor").post("/api/v1/writings", json=body)
        self.assertEqual(created.status_code, 200, created.text)
        self.assertEqual(created.json()["competency"], "WORTSCHATZ")
        self.assertEqual(self._client("editor").post("/api/v1/writings", json={**body, "competency": "HOEREN"}).status_code, 422)
        wid = created.json()["id"]
        self.assertEqual(self._client("support").put(f"/api/v1/writings/{wid}", json={"competency": None}).status_code, 403)
        self.assertIsNone(self._client("editor").put(f"/api/v1/writings/{wid}", json={"competency": None}).json()["competency"])

    # ---------- Schreiben history + analysis ----------

    def test_every_submitted_version_and_teacher_decision_is_kept(self):
        from app.services.student_writing import StudentWritingService

        lesson = self.lessons[1]
        task = self._writing(lesson, "Schreiben: E-Mail")
        svc = StudentWritingService(self.db)
        sid = self.user["student"].id
        first = svc.submit(sid, task.id, "Erste Version des Textes.", True)
        first.status = "NEEDS_REVISION"  # the teacher reopened it
        self.db.commit()
        svc.submit(sid, task.id, "Zweite, bessere Version.", True)
        history = svc.own_history(sid, task.id)
        self.assertEqual([v["attempt_number"] for v in history], [2, 1])
        self.assertEqual(history[1]["answer_text"], "Erste Version des Textes.")
        self.assertEqual(svc.own_history(self.user["other"].id, task.id), [])  # nobody else's

    def test_ai_analysis_keeps_every_run_and_never_invents_a_score(self):
        from app.models.lesson_skill import AiEvaluation
        from app.services.lesson_skills import ai_evaluation as ai
        from app.services.lesson_skills import levels
        from app.services.mock_exam.ai_service import AIServiceError
        from app.services.student_writing import StudentWritingService

        lesson = self.lessons[1]
        task = self._writing(lesson, "Schreiben: E-Mail", ai=True)
        sub = StudentWritingService(self.db).submit(self.user["student"].id, task.id, "Ich habe gestern ins Kino gegangen.", True)
        with patch.object(ai, "call_gemini_json", side_effect=AIServiceError("HTTP 503")):
            ai.evaluate_writing(self.db, sub.id)
        self.db.refresh(sub)
        self.assertEqual(sub.status, "EVALUATION_FAILED")
        self.assertIsNone(sub.score)
        self.assertIsNone(sub.ai_score)

        rubric = levels.writing_rubric("A2")
        raw = {"criteria": [{"key": c["key"], "score": c["max"], "comment": "gut", "tip": "weiter so"} for c in rubric],
               "errors": [{"original": "habe gestern ins Kino gegangen", "correction": "bin gestern ins Kino gegangen", "explanation": "sein",
                           "criterion": "grammar"}], "improved_text": "Ich bin gestern ins Kino gegangen."}
        with patch.object(ai, "call_gemini_json", return_value=(raw, "test-model")) as call:
            sub.status = "SUBMITTED"
            self.db.commit()
            ai.evaluate_writing(self.db, sub.id)
        self.assertIn("Satzbau", call.call_args[0][0])  # the A2 seven-criteria rubric was asked for
        self.db.refresh(sub)
        self.assertEqual((sub.status, sub.score), ("GRADED", 100))
        self.assertEqual(sub.ai_evaluation["errors"][0]["criterion"], "grammar")
        runs = list(self.db.query(AiEvaluation).filter(AiEvaluation.submission_id == sub.id).order_by(AiEvaluation.created_at))
        self.assertEqual([(r.status, r.attempt_number) for r in runs], [("FAILED", 1), ("SUCCEEDED", 1)])
        history = StudentWritingService(self.db).own_history(self.user["student"].id, task.id)
        self.assertEqual([e["status"] for e in history[0]["evaluations"]], ["FAILED", "SUCCEEDED"])
        self.assertEqual(history[0]["evaluations"][0]["error"], "AI_UNAVAILABLE")  # no provider detail to the student

    def test_lesen_open_questions_are_checked_against_the_reading_text(self):
        from app.models.reading import Reading
        from app.services.lesson_skills import ai_evaluation as ai
        from app.services.lesson_skills import levels
        from app.services.student_writing import StudentWritingService

        lesson = self.lessons[1]
        self.db.add(Reading(lesson_id=lesson.id, title="Text", content="Die Deutschen frühstücken gern Brötchen.", order_index=1, is_published=True,
                            content_id=f"{self.PREFIX}r1"))
        self.db.commit()
        task = self._writing(lesson, "Lesen: Fragen zum Text", "LESEN", ai=True)
        sub = StudentWritingService(self.db).submit(self.user["student"].id, task.id, "Sie essen Brötchen.", True)
        rubric = levels.competency_rubric("LESEN", "A2")
        raw = {"criteria": [{"key": c["key"], "score": c["max"], "comment": "ok"} for c in rubric]}
        with patch.object(ai, "call_gemini_json", return_value=(raw, "m")) as call:
            ai.evaluate_writing(self.db, sub.id)
        prompt = call.call_args[0][0]
        self.assertIn("Die Deutschen frühstücken gern Brötchen.", prompt)
        self.assertIn("Lesen (o'qish)", prompt)
        self.assertNotIn("Satzbau", prompt)
        self.db.delete(self.db.query(Reading).filter(Reading.content_id == f"{self.PREFIX}r1").one())
        self.db.commit()

    def test_teacher_decision_is_recorded_and_shown_as_teacher_reviewed(self):
        from app.models.lesson_skill import AiEvaluation
        from app.services.student_writing import StudentWritingService
        from app.services.lesson_skills import admin as skill_admin
        from app.models.lesson_skill import EVAL_KIND_WRITING

        lesson = self.lessons[1]
        task = self._writing(lesson, "Schreiben: E-Mail")
        sub = StudentWritingService(self.db).submit(self.user["student"].id, task.id, "Hallo Anna, wie geht es dir?", True)
        self.assertFalse(sub.teacher_reviewed)
        item = skill_admin.override_score(self.db, EVAL_KIND_WRITING, sub.id, self.user["super"], 80, "Gut gemacht.", "Lehrerbewertung")
        self.assertTrue(item["teacher_reviewed"])
        self.assertEqual(item["competency"], "SCHREIBEN")
        self.assertEqual(len(item["versions"]), 1)
        runs = self.db.query(AiEvaluation).filter(AiEvaluation.submission_id == sub.id).all()
        self.assertEqual([(r.source, r.score, r.attempt_number) for r in runs], [("MANUAL_OVERRIDE", 80, 1)])

    @unittest.skipUnless(HAS_HTTPX, "HTTP part needs httpx")
    def test_history_endpoint_is_own_only(self):
        from app.services.student_writing import StudentWritingService

        task = self._writing(self.lessons[1], "Schreiben: E-Mail")
        StudentWritingService(self.db).submit(self.user["student"].id, task.id, "Mein Text.", True)
        mine = self._client("student").get(f"/api/v1/writings/{task.id}/submissions/me/history").json()
        self.assertEqual(mine["versions"][0]["answer_text"], "Mein Text.")
        self.assertEqual(self._client("other").get(f"/api/v1/writings/{task.id}/submissions/me/history").json(), {"versions": []})
        self.assertEqual(self._client(None).get(f"/api/v1/writings/{task.id}/submissions/me/history").status_code, 401)

    # ---------- Wortschatz dictionary ----------

    @unittest.skipUnless(HAS_HTTPX, "HTTP part needs httpx")
    def test_student_dictionary_search_data_topics_and_own_state(self):
        free, paid = self.lessons[1], self.lessons[2]
        a = self._word(free, "Bewerbung", "ariza", "die", word_type="Nomen", plural="Bewerbungen", data_sources={"plural": "woerterbuch:A2-1"})
        self._word(free, "Entwurf", "qoralama", "der", published=False)
        b = self._word(paid, "Gehalt", "maosh", "das")
        client = self._client("student")
        data = client.get(f"/api/v1/lesson-skills/{free.id}/wortschatz/words").json()
        self.assertEqual([w["german_word"] for w in data["words"]], ["Bewerbung"])  # unpublished hidden
        first = data["words"][0]
        self.assertEqual((first["plural"], first["audio_text"], first["sources"]["plural"]), ("Bewerbungen", "die Bewerbung", "woerterbuch:A2-1"))
        self.assertEqual(first["missing"], ["example_sentence"])
        # level scope: only topics (lessons) open for this student — the paid lesson's words never leak
        level = client.get(f"/api/v1/lesson-skills/{free.id}/wortschatz/words?scope=level").json()
        self.assertEqual([t["number"] for t in level["topics"]], [1])
        self.assertNotIn("Gehalt", [w["german_word"] for w in level["words"]])

        saved = client.put(f"/api/v1/lesson-skills/{free.id}/wortschatz/words/{a.id}/state", json={"saved": True, "learned": True})
        self.assertEqual((saved.json()["saved"], saved.json()["learned"]), (True, True))
        self.assertFalse(self._client("other").get(f"/api/v1/lesson-skills/{free.id}/wortschatz/words").json()["words"][0]["saved"])
        self.assertEqual(client.put(f"/api/v1/lesson-skills/{free.id}/wortschatz/words/{b.id}/state", json={"saved": True}).status_code, 403)
        self.assertEqual(client.put(f"/api/v1/lesson-skills/{free.id}/wortschatz/words/{a.id}/state", json={"evil": 1}).status_code, 422)
        self.assertEqual(self._client(None).get(f"/api/v1/lesson-skills/{free.id}/wortschatz/words").status_code, 401)

    # ---------- CSV ----------

    def test_csv_export_import_roundtrip_and_all_or_nothing(self):
        from app.services.lesson_skills import word_csv

        lesson = self.lessons[1]
        a = self._word(lesson, "Bewerbung", "ariza", "die", order_index=3)
        exported = word_csv.export_csv(self.db, lesson.id).decode("utf-8-sig")
        self.assertIn("Bewerbung", exported)
        self.assertTrue(exported.splitlines()[0].startswith("id,german_word"))
        csv_text = ("id,german_word,article,plural,translation,word_type\n"
                    f"{a.id},Bewerbung,die,Bewerbungen,ish arizasi,Nomen\n"
                    ",Projekt,das,Projekte,loyiha,Nomen\n").encode()
        preview = word_csv.import_csv(self.db, lesson.id, csv_text, apply=False)
        self.assertEqual((preview["created"], preview["updated"], preview["applied"]), (1, 1, False))
        self.db.refresh(a)
        self.assertEqual(a.translation, "ariza")  # preview wrote nothing
        done = word_csv.import_csv(self.db, lesson.id, csv_text, apply=True)
        self.assertTrue(done["applied"])
        self.db.refresh(a)
        self.assertEqual((a.translation, a.plural, a.order_index, a.data_sources.get("plural")), ("ish arizasi", "Bewerbungen", 3, "admin"))
        bad = ("german_word,translation,article\nGut,yaxshi,xyz\nNeu,yangi,\n").encode()
        report = word_csv.import_csv(self.db, lesson.id, bad, apply=True)
        self.assertFalse(report["applied"])
        self.assertTrue(report["errors"][0].startswith("line 2:"))
        foreign = self._word(self.lessons[2], "Fremd", "begona")
        self.assertIn("not a word of this lesson", word_csv.import_csv(self.db, lesson.id, f"id,german_word,translation\n{foreign.id},X,y\n".encode(),
                                                                         apply=False)["errors"][0])

    @unittest.skipUnless(HAS_HTTPX, "HTTP part needs httpx")
    def test_csv_endpoints_need_the_right_role(self):
        lesson = self.lessons[1]
        files = {"file": ("w.csv", b"german_word,translation\nHaus,uy\n", "text/csv")}
        self.assertEqual(self._client("support").post(f"/api/v1/admin/lesson-skills/lessons/{lesson.id}/words/import", files=files).status_code, 403)
        self.assertEqual(self._client("student").get(f"/api/v1/admin/lesson-skills/lessons/{lesson.id}/words.csv").status_code, 403)
        ok = self._client("editor").post(f"/api/v1/admin/lesson-skills/lessons/{lesson.id}/words/import", files=files, data={"apply": "true"})
        self.assertEqual(ok.status_code, 200, ok.text)
        self.assertEqual(ok.json()["created"], 1)
        export = self._client("support").get(f"/api/v1/admin/lesson-skills/lessons/{lesson.id}/words.csv")
        self.assertEqual(export.status_code, 200)
        self.assertIn("Haus", export.content.decode("utf-8-sig"))

    # ---------- the data step ----------

    def _entry(self, lemma, article, word_type, **kw):
        import hashlib

        from app.models.dictionary import DictionaryEntry

        e = DictionaryEntry(level="A2", source_id=900000 + uuid.uuid4().int % 90000, lemma=lemma, article=article, word_type=word_type,
                            translation="x", status=kw.pop("status", "verified"), group_key=f"{article} {lemma}", search_de=lemma.lower(),
                            search_uz="x", content_hash=hashlib.sha256(lemma.encode()).hexdigest(), extra={}, **kw)
        self.db.add(e)
        self.db.commit()
        return e

    def test_plan_apply_moves_tasks_enriches_words_creates_tests_once(self):
        from app.models.lesson_skill import SkillExercise
        from app.services.lesson_skills.results import lesson_skill_results
        from app.services.lms import a2_module_separation as sep

        lesson = self.lessons[1]
        schreiben = self._writing(lesson, "Schreiben: Mein Traumberuf", content_id="vizu-a2buch-l01-schreiben-01", rubric=[{"key": "a", "name": "A", "max": 100}])
        grammatik = self._writing(self.lessons[2], "Grammatik-Aufgabe: WENN", content_id="vizu-a2buch-l02-schreiben-02")
        self._entry("Testwortnomen", "die", "Nomen", plural="Testwortnomen-n", example_de="Die Testwortnomen ist da.", example_uz="Bor.")
        self._entry("testarbeiten", None, "Verb", verb_praeteritum="testarbeitete", verb_partizip_ii="getestarbeitet", verb_auxiliary="haben")
        self._entry("Testwortfalsch", "der", "Nomen", plural="NEIN", status="needs_review")
        nouns = [self._word(lesson, "Testwortnomen", "test ot", "die", order_index=1),
                 self._word(lesson, "Testwortfalsch", "noto'g'ri", "der", order_index=2),
                 self._word(lesson, "testarbeiten", "sinab ishlamoq", order_index=3)]
        for i, (german, tr, art) in enumerate([("Haus", "uy", "das"), ("Auto", "mashina", "das"), ("Tisch", "stol", "der"), ("Lampe", "chiroq", "die")]):
            self._word(lesson, german, tr, art, order_index=10 + i)

        result = sep.plan(self.db)
        info = sep.summary(result)
        self.assertEqual(info["writings_moved"], {"GRAMMATIK": 1})
        self.assertEqual(info["writings_rubric_reset"], 1)
        with self.assertRaises(RuntimeError):
            sep.apply(self.db, Path(self.tmp.name), "000000000000")
        report = sep.apply(self.db, Path(self.tmp.name), result["plan_id"])
        self.assertTrue((Path(report["backup"]) / "backup.json").exists())

        self.db.refresh(schreiben)
        self.db.refresh(grammatik)
        self.assertEqual((schreiben.competency, schreiben.rubric), (None, None))
        self.assertEqual(grammatik.competency, "GRAMMATIK")
        for v in nouns:
            self.db.refresh(v)
        self.assertEqual((nouns[0].plural, nouns[0].data_sources["plural"][:12]), ("Testwortnomen-n", "woerterbuch:"))
        self.assertIsNone(nouns[1].plural)  # a needs_review entry is never used
        self.assertEqual(nouns[1].data_sources, {"word_type": "book:article"})
        self.assertEqual((nouns[2].word_type, nouns[2].verb_partizip_ii, nouns[2].verb_auxiliary), ("Verb", "getestarbeitet", "haben"))

        sets = list(self.db.query(SkillExercise).filter(SkillExercise.lesson_id == lesson.id, SkillExercise.skill == "WORTSCHATZ"))
        self.assertTrue(sets)
        self.assertTrue(all(s.is_published and s.source == "vizu" and s.content_id.startswith("vizu-a2buch-l01-wortschatz-test-") for s in sets))
        again = sep.summary(sep.plan(self.db))
        self.assertEqual((again["writings_moved"], again["words_changed"], again["test_sets"]), ({}, 0, 0))  # idempotent

        # the generated tests are graded on the server and decide Wortschatz progress
        skills = lesson_skill_results(self.db, self.user["student"].id, lesson.id)["skills"]
        self.assertEqual(skills["wortschatz"]["status"], "not_started")
        self.assertEqual(len(skills["wortschatz"]["tasks"]), len(sets))

    @unittest.skipUnless(HAS_HTTPX, "HTTP part needs httpx")
    def test_generated_test_is_scored_on_the_server_without_leaking_the_key(self):
        from app.services.content_import.service import _add_exercise
        from app.models.lesson_skill import SkillExercise
        from app.services.lesson_skills import admin as skill_admin
        from app.services.lesson_skills import wortschatz_tests as wt

        lesson = self.lessons[1]
        artikel = next(s for s in wt.build_sets(NOUNS) if s["key"] == "artikel")
        ref = _add_exercise(self.db, lesson.id, "WORTSCHATZ", {**artikel, "questions": skill_admin.validate_questions(artikel["questions"])},
                            f"{self.PREFIX}artikel")
        self.db.get(SkillExercise, ref["id"]).is_published = True
        self.db.commit()
        client = self._client("student")
        view = client.get(f"/api/v1/lesson-skills/{lesson.id}/exercises/wortschatz").json()
        ex = view["exercises"][0]
        self.assertNotIn("is_correct", str(ex["questions"]))
        attempt = client.post(f"/api/v1/lesson-skills/{lesson.id}/exercises/wortschatz/{ex['id']}/start").json()
        by_text = {q["question"]: q for q in ex["questions"]}
        q = by_text["___ Bewerbung"]
        die = next(o["id"] for o in q["options"] if o["text"] == "die")
        der = next(o["id"] for o in q["options"] if o["text"] == "der")
        answers = {q["id"]: die, by_text["___ Projekt"]["id"]: der}  # one right, one wrong, the rest unanswered
        result = client.post(f"/api/v1/lesson-skills/{lesson.id}/exercises/wortschatz/{ex['id']}/submit",
                             json={"attempt_id": attempt["id"], "answers": answers}).json()
        self.assertEqual(result["correct_count"], 1)
        self.assertEqual(result["question_count"], len(ex["questions"]))
        self.assertEqual(result["score"], round(100 / len(ex["questions"])))


@unittest.skipUnless(os.environ.get("VIZU_MIGRATION_TEST_DB_URL"), "migration test: set VIZU_MIGRATION_TEST_DB_URL")
class TestModuleSeparationMigration(unittest.TestCase):
    REV, PREVIOUS = "d7e2b4f8a1c6", "c4f7a9e2d6b3"

    def setUp(self):
        from alembic.config import Config
        from sqlalchemy import create_engine

        self.url = os.environ["VIZU_MIGRATION_TEST_DB_URL"]
        self.cfg = Config()
        self.cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
        self.engine = create_engine(self.url)

    def tearDown(self):
        self._alembic("upgrade", "head")
        self.engine.dispose()

    def _alembic(self, action, rev):
        from alembic import command
        from sqlalchemy.engine import make_url

        from app.core.config import settings

        u = make_url(self.url)
        with patch.multiple(settings, DATABASE_HOST=u.host, DATABASE_PORT=u.port or 5432, DATABASE_NAME=u.database,
                            DATABASE_USER=u.username, DATABASE_PASSWORD=u.password or ""):
            getattr(command, action)(self.cfg, rev)

    def _columns(self, table):
        from sqlalchemy import text

        with self.engine.begin() as c:
            return {r[0] for r in c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = :t"), {"t": table})}

    def test_upgrade_downgrade_upgrade(self):
        from sqlalchemy import text

        self._alembic("upgrade", "head")
        self.assertIn("competency", self._columns("writings"))
        self.assertIn("verb_partizip_ii", self._columns("vocabularies"))
        self.assertIn("attempt_number", self._columns("ai_evaluations"))
        self.assertTrue(self._columns("student_writing_versions"))
        with self.engine.begin() as c:
            check = c.execute(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'ck_writings_competency'")).scalar()
        self.assertIn("LESEN", check)
        self._alembic("downgrade", self.PREVIOUS)
        self.assertNotIn("competency", self._columns("writings"))
        self.assertFalse(self._columns("vocabulary_user_words"))
        self.assertFalse(self._columns("student_writing_versions"))
        self._alembic("upgrade", self.REV)
        self.assertIn("competency", self._columns("writings"))


if __name__ == "__main__":
    unittest.main()
