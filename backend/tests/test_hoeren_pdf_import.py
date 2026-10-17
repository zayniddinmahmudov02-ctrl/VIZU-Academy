"""A1 Hören answer-sheet PDF: block detection and answer parsing (no DB)."""

import unittest

from app.services.lesson_skills import hoeren_pdf_import as h

SHEET = """@vizu_academy
1-Dars
Vazifalar to`liq O`qituvchi tomonidan tekshiriladi.
2-Dars
Grammatik
1 b, 2 a, 3 a
Lesen - O`qish qismi javoblari:
1 B, 2 A
Hören – Eshitish qismi javoblari:
Peter, Berlin, Familie,
Vater, arbeitet
Schreiben und Sprechen – Yozish va Gapirish qismi Ustoz tomonidan tekshiriladi.
3-4-Darslar
Lesen - O`qish va Hören – Eshitish qismlari uchun ovozli yuborasiz.
5-Dars
Hören – Eshitish qismi javoblari:
Samstag: 08:00, 08:30
Sonntag: 09:00
Schreiben – Yozish
7-Dars
8) hört → hat gehört
Hören – Eshitish qismi javoblari:
Mein Tag in Taschkent matni javoblari:
war, kam, war
@vizu_academy
"""


class TestBlocks(unittest.TestCase):
    def test_only_hoeren_blocks_are_read(self):
        blocks = h.hoeren_blocks(SHEET)
        self.assertEqual([(b.lessons, bool(b.text)) for b in blocks], [([2], True), ([3, 4], False), ([5], True), ([7], True)])
        two = blocks[0].text
        self.assertIn("Peter", two)
        self.assertNotIn("1 B", two)  # Lesen answers never leak in
        self.assertNotIn("Schreiben", two)

    def test_title_line_is_not_an_answer(self):
        blocks = h.hoeren_blocks(SHEET)
        groups = h.parse_groups(blocks[3].text)
        self.assertEqual([a["text"] for g in groups for a in g.answers], ["war", "kam", "war"])


class TestGroups(unittest.TestCase):
    def answers(self, text):
        return [[a["text"] for a in g.answers] for g in h.parse_groups(text)]

    def test_formats(self):
        self.assertEqual(self.answers("Samstag: 08:00, 08:30\nSonntag: 09:00"), [["08:00", "08:30"], ["09:00"]])
        self.assertEqual(self.answers("1) das Brot, 2) die Butter, 3) der Käse"), [["das Brot", "die Butter", "der Käse"]])
        self.assertEqual(self.answers("Text 1: 1-b, 2-c   Text 2: 1-b, 2-b"), [["b", "c"], ["b", "b"]])
        self.assertEqual(self.answers("1-B, 2-A, 3-B"), [["B", "A", "B"]])
        self.assertEqual(self.answers("Wetterbericht 1: Berlin — 8 — Hamburg"), [["Berlin", "8", "Hamburg"]])
        self.assertEqual(self.answers("bin geflogen; habe gemacht; war; möchte hinfahren."), [["bin geflogen", "habe gemacht", "war", "möchte hinfahren"]])
        self.assertEqual(self.answers("1) Alisa 2) Alex 3) Alisa"), [["Alisa", "Alex", "Alisa"]])

    def test_name_hint_before_arrow(self):
        g = h.parse_groups("1. Markus Klein → B   2. Leon Schmidt → A")[0]
        self.assertEqual([(a["hint"], a["text"]) for a in g.answers], [("Markus Klein", "B"), ("Leon Schmidt", "A")])

    def test_broken_numbering_is_reported_not_guessed(self):
        g = h.parse_groups("1) a 3) b 4) c")[0]
        self.assertTrue(g.problem)
        self.assertEqual(g.answers, [])


class TestVariants(unittest.TestCase):
    def test_article_and_time_spellings(self):
        self.assertEqual(h._variants("das Brot"), ["das Brot", "Brot"])
        self.assertEqual(set(h._variants("08:00")), {"08:00", "8:00", "08.00", "8.00"})
        self.assertEqual(h._variants("Berlin"), ["Berlin"])

    def test_neighbour_words_ignore_verb_hint(self):
        text = "Das Hotel [[7]] (haben) mir sehr gut [[8]] (gefallen). Ich [[2]] in Berlin."
        self.assertNotIn("gefallen", h._neighbour_words(text, "8"))
        self.assertIn("berlin", h._neighbour_words(text, "2"))

    def test_not_a_pdf(self):
        with self.assertRaises(h.PdfImportError):
            h.pdf_text(b"hello")


if __name__ == "__main__":
    unittest.main()
