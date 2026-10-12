"""Contract: the lesson step order ("Kompetenzen") is defined once per side —
frontend `lessonSections` (src/constants/lesson-sections.ts, rendered in that
order by the sidebar, which only filters, never sorts) and backend
GATED_ORDER (section_gate.py, lesson completion). Mapped through the
frontend's SECTION_GATE_KEYS, the two must be the same sequence."""

import re
import unittest
from pathlib import Path

from app.services.lesson_progress.section_gate import GATED_ORDER

SECTIONS_TS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "constants" / "lesson-sections.ts"


@unittest.skipUnless(SECTIONS_TS.exists(), "frontend checkout not present")
class TestSectionOrderContract(unittest.TestCase):
    def setUp(self):
        self.source = SECTIONS_TS.read_text(encoding="utf-8")

    def _section_types(self) -> list[str]:
        block = re.search(r"export const lessonSections[^=]*=\s*\[(.*?)\n\];", self.source, re.S).group(1)
        return re.findall(r'type:\s*"([^"]+)"', block)

    def _gate_keys(self) -> dict[str, str | None]:
        block = re.search(r"export const SECTION_GATE_KEYS[^=]*=\s*\{(.*?)\n\};", self.source, re.S).group(1)
        return {
            k.strip('"'): (None if v == "null" else v.strip('"'))
            for k, v in re.findall(r'("?[\w-]+"?):\s*("[\w-]+"|null)', block)
        }

    def test_frontend_order_matches_backend_gated_order(self):
        keys = self._gate_keys()
        mapped = [keys[t] for t in self._section_types() if keys.get(t)]
        self.assertEqual(mapped, GATED_ORDER)

    def test_video_first_results_last(self):
        types = self._section_types()
        self.assertEqual(types[0], "video")
        self.assertEqual(types[-1], "results")
        self.assertEqual(len(types), len(set(types)))


if __name__ == "__main__":
    unittest.main()
