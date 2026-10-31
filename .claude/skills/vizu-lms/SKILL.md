---
name: vizu-lms
description: VIZU A1–C1 course work — levels, lessons, the 10 competencies, Lesen/Hören/Grammatik/Wortschatz/Schreiben/Sprechen tasks, answer keys (Lösung), scoring, progress, unlock rules, content import. Use for any change to course content or the student lesson player.
---
# VIZU LMS

## Context to load (in this order, stop when enough)
1. `docs/ai-context/module-registry.md` → the module(s): LMS, the competency module (Lesen/Hören/…),
   Progress & Scoring.
2. Level specifics: `docs/a2-*.md`, `docs/lms-architecture.md` only for the level/topic in question.
3. Source: start at the service named in the module entry; open the router only for the endpoint you touch.

## Facts you need most
- Structure: course → main module → lessons (`services/lms/structure.py`, `LEVEL_LESSON_COUNTS`) →
  competencies (`models/lms.py:COMPETENCY_ORDER`). Content rows keep a stable `content_id`
  (`vizu-a1-…`, `vizu-a2buch-…`); `[Archiv] …` rows are the old edition (hidden).
- Book editions are generated from Python sources: `app/scripts/vizu_deutsch_a2/` (first edition),
  `vizu_deutsch_a2_buch/` (book edition, `DROP`, `FIXES`) → `app/data/*.json` via `…build`, imported with
  `import_vizu_deutsch_a1` / `import_vizu_deutsch_a2_buch` (`skip_existing`, re-run safe).
- Keys: `services/lesson_skills/loesung.py` (VERIFIED needs a matching fingerprint; NEEDS_REVIEW blocks
  publishing). Write keys with `scripts/a1_hoeren_keys.plan_task/apply_question` (editor validation).
- Hören publish rule: audio file on disk + every key verified (`hoeren_pdf_import.readiness`).
- Results/progress: `lesson_skills/results.py`, `learning/lesson_progress.py`, `lms/progress.py`; a
  competency without published content does not count for completion.

## Workflow
1. Reproduce with the smallest query/test. 2. Change the service, not the router. 3. Never invent book
content, questions or keys — mark NEEDS_REVIEW with the reason. 4. Tests: the module's test file
(`tests/test_lms_*`, `test_lesson_skills`, `test_loesung`, `test_a2_*`), plus `test_route_protection`
if access changed. 5. Update the module entry + `recent-changes.md`.
