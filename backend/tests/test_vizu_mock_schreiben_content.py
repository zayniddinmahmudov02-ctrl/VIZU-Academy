"""VIZU-Mock Schreiben — the 5 standard Aufgaben must match the specification
exactly (order, topics, word limits, rubric, key task text)."""

import unittest

from app.services.vizu_multilevel import schreiben_content as content
from app.services.vizu_multilevel import schreiben_evaluation_service as evaluation


class TestSchreibenContent(unittest.TestCase):
    def test_exactly_five_in_order(self):
        self.assertEqual([t["order"] for t in content.TASKS], [1, 2, 3, 4, 5])

    def test_topics_and_word_limits(self):
        self.assertEqual(
            [(t["title"], t["min_words"], t["max_words"]) for t in content.TASKS],
            [
                ("Eine Nachricht an einen Freund", 30, 40),
                ("E-Mail an einen Sprachkurs", 50, 70),
                ("Antwort auf eine E-Mail", 80, 100),
                ("Beitrag für ein Online-Forum", 120, 150),
                ("Stellungnahme", 180, 220),
            ],
        )

    def test_rubrics_sum_to_20_and_total_100(self):
        for t in content.TASKS:
            self.assertEqual(sum(m for _, m in t["rubric"]), 20)
        self.assertEqual(content.POINTS_PER_TASK * len(content.TASKS), 100)

    def test_rubric_criteria_match_spec(self):
        self.assertEqual(content.TASKS[1]["rubric"][4], ("Rechtschreibung/Form", 3))
        self.assertEqual(content.TASKS[2]["rubric"][3], ("Textaufbau/Kohärenz", 3))
        self.assertEqual(content.TASKS[3]["rubric"][0], ("Aufgabenbearbeitung und Inhalt", 5))
        self.assertEqual(content.TASKS[4]["rubric"][3], ("Textaufbau, Kohärenz und Verknüpfungen", 4))

    def test_full_task_texts(self):
        texts = [t["instruction"] for t in content.TASKS]
        self.assertIn("- was ihr zusammen machen möchtet", texts[0])
        self.assertIn("- Wie viel kostet der Kurs?", texts[1])
        self.assertIn("Du hast folgende E-Mail von deinem Freund / deiner Freundin bekommen:", texts[2])
        self.assertIn("- einen Vorschlag für einen Tag", texts[2])
        self.assertIn("Du schreibst einen Beitrag in einem Online-Forum zum Thema:", texts[3])
        self.assertIn("Du liest folgende Aussage:", texts[4])
        self.assertIn("- abschließende Schlussfolgerung", texts[4])
        self.assertIn("Argumentiere klar und strukturiert.", texts[4])
        for t, text in zip(content.TASKS, texts):
            self.assertTrue(text.endswith(f"Schreibe {t['min_words']}–{t['max_words']} Wörter."))


class TestPerAreaComments(unittest.TestCase):
    def test_clean_text(self):
        self.assertEqual(evaluation._clean_text("  gut  "), "gut")
        self.assertEqual(evaluation._clean_text(None), "")
        self.assertEqual(evaluation._clean_text(["x"]), "")
        self.assertEqual(len(evaluation._clean_text("a" * 2000)), 800)

    def test_empty_result_has_all_comment_keys(self):
        task = type("T", (), {"rubric_criteria": []})()
        result = evaluation._empty_result(task)
        for key in evaluation.COMMENT_KEYS:
            self.assertIn(key, result)


if __name__ == "__main__":
    unittest.main()
