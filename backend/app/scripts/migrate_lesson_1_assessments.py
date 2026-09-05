"""Review-first migration: copies A1 Lesson 1's Hören/Schreiben/Sprechen
content out of the LEGACY, student-UI-unused `listenings`/`writings`/
`speakings` tables into the Universal Assessment Engine (`assessments` ->
`assessment_sections` -> `assessment_tasks`), which is what the student
lesson player and SectionGateService._skill_applicable actually read.

Root cause this fixes: reading-section.tsx/listening-section.tsx/
writing-section.tsx/speaking-section.tsx and section_gate.py's
_skill_applicable all query the Assessment Engine exclusively — the
legacy tables (still populated by seed_lesson_1.py, and still editable
from the admin lesson page's "(Legacy)" tabs) are never read by any of
that code. This script does not touch seed_lesson_1.py or the legacy
rows at all — it only reads them and writes their content, once, into
the engine, mirroring exactly the shape the admin's own
LesenAssessmentManager (frontend/src/features/admin/components/lesen/
lesen-assessment-manager.tsx) creates when an admin clicks "+ Aufgabe
hinzufügen" by hand: one shared COURSE Assessment per lesson, one
AssessmentSection per skill, one AssessmentTask per legacy content row.

Mapping (legacy field -> AssessmentTask field), same shape the admin UI
itself writes for each task_type:
  Hören (Listening -> task_type=MULTIPLE_CHOICE):
    title -> title, transcript -> content, order_index -> sort_order.
    No TaskAudio row is ever created (no real audio file exists — never
    fabricated) and no TaskQuestion rows either (no real comprehension
    questions exist in the source material — never invented). status is
    always left DRAFT, regardless of --dry-run vs real run: with no
    audio, this task is not ready to publish, and the admin UI itself
    has no per-task publish control in LesenAssessmentManager (only
    Assessment-level; see PUBLISH_ON_CREATE below) — so DRAFT is both
    the safe and the structurally consistent choice.
  Schreiben (Writing -> task_type=WRITING):
    title -> title, instruction -> content, min_words/max_words ->
    min_words/max_words, order_index -> sort_order,
    evaluation_mode="AI_ONLY" (the schema/admin default for WRITING).
  Sprechen (Speaking -> task_type=SPEAKING):
    title -> title, topic -> instructions (the short guidance line the
    admin UI's own "Anweisung für Lernende" field is for), instruction ->
    content, preparation_time -> prep_seconds, speaking_time ->
    speak_seconds, order_index -> sort_order,
    evaluation_mode="TEACHER_ONLY" (the schema/admin default the manager
    itself applies for every SPEAKING task).

PUBLISH_ON_CREATE and why Schreiben/Sprechen are set PUBLISHED here even
though LesenAssessmentManager's own "createTask" call never passes a
status (so a task made by hand through that exact UI defaults to DRAFT
forever — that component only ever toggles the shared Assessment's
status, it has no per-task publish button at all, unlike the separate
Vorbereitung task-manager.tsx, which does). Since the whole point of
this migration is for Hören/Schreiben/Sprechen to actually reach
students, and PUBLISHED is a state this exact same system already uses
elsewhere for exactly this field (AssessmentTaskUpdate.status), setting
it here is applying an existing, valid transition — not inventing one.
Hören is the one deliberate exception (see above). This is a real,
consequential product decision, not a default to wave through — it is
called out again in both --dry-run output and the script's final
summary so whoever runs this for real makes the choice consciously; set
PUBLISH_ON_CREATE below to False for any skill to leave it DRAFT
instead. This is also a separate, pre-existing gap worth flagging on its
own: as it stands, nothing built through LesenAssessmentManager (Lesen
included) can ever be published at the per-task level from that UI —
this script does not fix that gap, it only works around it for the
three tasks it creates here.

Neither Schreiben nor Sprechen tasks get a WritingRubricCriterion here —
that also matches a task freshly created by hand through the admin UI
(criteria are added afterwards, per task, from WritingPanel/
SpeakingPanel). Add at least one via the admin Schreiben/Sprechen tab
before relying on real scoring — flagged again in the summary output.

IDEMPOTENT, ADDITIVE, REVIEW-FIRST — matches seed_courses.py's pattern
in spirit, kept in a wholly separate script/module (never imports from
or modifies seed_lesson_1.py, and never writes to the legacy
listenings/writings/speakings tables):
  - The lesson's one COURSE Assessment is reused if it already exists
    (it does, from the existing Lesen content) — never duplicated.
  - Each skill's AssessmentSection is reused if it already exists —
    never duplicated.
  - Each AssessmentTask is matched by (section_id, title) before
    insert — an already-migrated (or independently admin-created) task
    with the same title is left completely untouched (no update, no
    overwrite of any field), only genuinely missing ones are created.
  - Nothing is ever deleted, and no existing Assessment/Section/Task
    (whatever its status or origin) is ever modified.

Run from the `backend/` directory — dry-run first, always:

    python -m app.scripts.migrate_lesson_1_assessments --dry-run
    python -m app.scripts.migrate_lesson_1_assessments
"""

import argparse
from dataclasses import dataclass, field
from uuid import UUID

import app.models  # noqa: F401 — registers every model with Base before querying

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.assessment import STATUS_DRAFT, STATUS_PUBLISHED, TYPE_COURSE, Assessment
from app.models.assessment_section import (
    SKILL_HOEREN,
    SKILL_SCHREIBEN,
    SKILL_SPRECHEN,
    AssessmentSection,
)
from app.models.assessment_task import (
    TYPE_MULTIPLE_CHOICE,
    TYPE_SPEAKING,
    TYPE_WRITING,
    AssessmentTask,
)
from app.models.course import Course
from app.models.language import Language
from app.models.lesson import Lesson
from app.models.listening import Listening
from app.models.module import Module
from app.models.speaking import Speaking
from app.models.writing import Writing

LEVEL = "A1"
LESSON_NUMBER = 1

SECTION_TITLES = {
    SKILL_HOEREN: "Hören",
    SKILL_SCHREIBEN: "Schreiben",
    SKILL_SPRECHEN: "Sprechen",
}

# See the module docstring's "PUBLISH_ON_CREATE" section for the full
# reasoning. Hören is never published regardless of this map — no real
# audio exists yet, enforced unconditionally in build_plan(), not just
# defaulted here.
PUBLISH_ON_CREATE = {
    SKILL_HOEREN: False,
    SKILL_SCHREIBEN: True,
    SKILL_SPRECHEN: True,
}


def find_lesson_1(db):
    language = db.scalar(select(Language).where(Language.code == "de", Language.deleted_at.is_(None)))
    if language is None:
        return None
    course = db.scalar(select(Course).where(Course.language_id == language.id, Course.level == LEVEL))
    if course is None:
        return None
    module = db.scalar(select(Module).where(Module.course_id == course.id))
    if module is None:
        return None
    return db.scalar(select(Lesson).where(Lesson.module_id == module.id, Lesson.number == LESSON_NUMBER))


# ==========================
# Plan — a single, pure, read-only pass over the DB. Both --dry-run and
# the real run build the exact same plan from the exact same queries;
# only apply_plan() (never called in --dry-run) writes anything. This is
# what guarantees dry-run output can never diverge from what a real run
# would actually do.
# ==========================


@dataclass
class TaskPlan:
    skill: str
    legacy_id: UUID
    title: str
    already_exists: bool
    task_type: str
    content: str | None
    instructions: str | None = None
    min_words: int | None = None
    max_words: int | None = None
    prep_seconds: int | None = None
    speak_seconds: int | None = None
    evaluation_mode: str = "AI_ONLY"
    sort_order: int = 1
    publish: bool = False


@dataclass
class SectionPlan:
    skill: str
    already_exists: bool
    existing_id: UUID | None
    tasks: list[TaskPlan] = field(default_factory=list)


@dataclass
class MigrationPlan:
    lesson_id: UUID
    assessment_already_exists: bool
    assessment_id: UUID | None
    assessment_status: str | None
    sections: list[SectionPlan] = field(default_factory=list)

    def to_create_count(self) -> int:
        return sum(1 for s in self.sections for t in s.tasks if not t.already_exists)


def _existing_task_titles(db, section_id: UUID) -> set[str]:
    return {
        row[0]
        for row in db.query(AssessmentTask.title).filter(AssessmentTask.section_id == section_id).all()
    }


def build_plan(db, lesson: Lesson) -> MigrationPlan:
    assessment = db.scalar(
        select(Assessment)
        .where(Assessment.lesson_id == lesson.id, Assessment.assessment_type == TYPE_COURSE)
        .order_by(Assessment.created_at.desc())
    )
    plan = MigrationPlan(
        lesson_id=lesson.id,
        assessment_already_exists=assessment is not None,
        assessment_id=assessment.id if assessment else None,
        assessment_status=assessment.status if assessment else None,
    )

    def existing_section(skill: str) -> AssessmentSection | None:
        if assessment is None:
            return None
        return db.scalar(
            select(AssessmentSection).where(
                AssessmentSection.assessment_id == assessment.id, AssessmentSection.skill == skill
            )
        )

    # ---- Hören ----
    hoeren_section = existing_section(SKILL_HOEREN)
    hoeren_plan = SectionPlan(
        skill=SKILL_HOEREN,
        already_exists=hoeren_section is not None,
        existing_id=hoeren_section.id if hoeren_section else None,
    )
    existing_titles = _existing_task_titles(db, hoeren_section.id) if hoeren_section else set()
    listenings = db.scalars(
        select(Listening).where(Listening.lesson_id == str(lesson.id)).order_by(Listening.order_index)
    ).all()
    for listening in listenings:
        hoeren_plan.tasks.append(
            TaskPlan(
                skill=SKILL_HOEREN,
                legacy_id=listening.id,
                title=listening.title,
                already_exists=listening.title in existing_titles,
                task_type=TYPE_MULTIPLE_CHOICE,
                content=listening.transcript,
                sort_order=listening.order_index,
                publish=False,  # never — see module docstring
            )
        )
    plan.sections.append(hoeren_plan)

    # ---- Schreiben ----
    schreiben_section = existing_section(SKILL_SCHREIBEN)
    schreiben_plan = SectionPlan(
        skill=SKILL_SCHREIBEN,
        already_exists=schreiben_section is not None,
        existing_id=schreiben_section.id if schreiben_section else None,
    )
    existing_titles = _existing_task_titles(db, schreiben_section.id) if schreiben_section else set()
    writings = db.scalars(
        select(Writing).where(Writing.lesson_id == str(lesson.id)).order_by(Writing.order_index)
    ).all()
    for writing in writings:
        schreiben_plan.tasks.append(
            TaskPlan(
                skill=SKILL_SCHREIBEN,
                legacy_id=writing.id,
                title=writing.title,
                already_exists=writing.title in existing_titles,
                task_type=TYPE_WRITING,
                content=writing.instruction,
                min_words=writing.min_words,
                max_words=writing.max_words,
                evaluation_mode="AI_ONLY",
                sort_order=writing.order_index,
                publish=PUBLISH_ON_CREATE[SKILL_SCHREIBEN],
            )
        )
    plan.sections.append(schreiben_plan)

    # ---- Sprechen ----
    sprechen_section = existing_section(SKILL_SPRECHEN)
    sprechen_plan = SectionPlan(
        skill=SKILL_SPRECHEN,
        already_exists=sprechen_section is not None,
        existing_id=sprechen_section.id if sprechen_section else None,
    )
    existing_titles = _existing_task_titles(db, sprechen_section.id) if sprechen_section else set()
    speakings = db.scalars(
        select(Speaking).where(Speaking.lesson_id == str(lesson.id)).order_by(Speaking.order_index)
    ).all()
    for speaking in speakings:
        content = speaking.instruction
        extra_notes = [note for note in (speaking.sample_answer, speaking.keywords) if note]
        if extra_notes:
            content = content + "\n\n---\n" + "\n".join(extra_notes)
        sprechen_plan.tasks.append(
            TaskPlan(
                skill=SKILL_SPRECHEN,
                legacy_id=speaking.id,
                title=speaking.title,
                already_exists=speaking.title in existing_titles,
                task_type=TYPE_SPEAKING,
                content=content,
                instructions=speaking.topic,
                prep_seconds=speaking.preparation_time,
                speak_seconds=speaking.speaking_time,
                evaluation_mode="TEACHER_ONLY",
                sort_order=speaking.order_index,
                publish=PUBLISH_ON_CREATE[SKILL_SPRECHEN],
            )
        )
    plan.sections.append(sprechen_plan)

    return plan


def print_plan(plan: MigrationPlan) -> None:
    print(f"Lesson id: {plan.lesson_id}")
    if plan.assessment_already_exists:
        print(f"Assessment: reuse existing id={plan.assessment_id} status={plan.assessment_status}")
    else:
        print("Assessment: none exists yet - would CREATE one (status=DRAFT, title='Lektion Aufgaben')")
        print(
            "  WARNING: a freshly created Assessment defaults to DRAFT. Its "
            "sections/tasks will not reach students until an admin also "
            "publishes the Assessment itself from the Lesen/Hoeren/"
            "Schreiben/Sprechen tab."
        )

    for section in plan.sections:
        if section.already_exists:
            print(f"\n[{section.skill}] Section: reuse existing id={section.existing_id}")
        else:
            print(f"\n[{section.skill}] Section: none exists yet - would CREATE")

        if not section.tasks:
            print(f"  No legacy content found for {section.skill} - nothing to migrate.")
            continue

        to_create = [t for t in section.tasks if not t.already_exists]
        to_skip = [t for t in section.tasks if t.already_exists]
        print(f"  {len(section.tasks)} legacy row(s) found: {len(to_create)} to create, {len(to_skip)} already migrated (skip).")

        for task in to_skip:
            print(f"    SKIP  (already exists) title={task.title!r}")
        for task in to_create:
            status = "PUBLISHED" if task.publish else "DRAFT"
            print(f"    CREATE title={task.title!r} task_type={task.task_type} status={status}")
            if task.task_type == TYPE_MULTIPLE_CHOICE:
                has_transcript = "yes" if task.content else "NO TRANSCRIPT"
                print(f"            content(transcript)={has_transcript}, audio=NONE (never fabricated), questions=NONE")
            if task.task_type == TYPE_WRITING:
                print(f"            min_words={task.min_words} max_words={task.max_words} evaluation_mode={task.evaluation_mode}")
                print("            NOTE: no rubric criteria created - add at least one via the admin Schreiben tab before real grading.")
            if task.task_type == TYPE_SPEAKING:
                print(f"            prep_seconds={task.prep_seconds} speak_seconds={task.speak_seconds} evaluation_mode={task.evaluation_mode}")
                print("            NOTE: no rubric criteria created - add at least one via the admin Sprechen tab before real grading.")

    print()
    print(f"Total tasks to create: {plan.to_create_count()}")
    if any(t.publish for s in plan.sections for t in s.tasks if not t.already_exists):
        print(
            "NOTE: Schreiben/Sprechen tasks are created PUBLISHED (Hoeren always stays DRAFT - "
            "see module docstring's PUBLISH_ON_CREATE section for why). Review this before a real run."
        )


def apply_plan(db, plan: MigrationPlan) -> None:
    if plan.assessment_id is not None:
        assessment_id = plan.assessment_id
    else:
        assessment = Assessment(
            title="Lektion Aufgaben",
            assessment_type=TYPE_COURSE,
            lesson_id=plan.lesson_id,
            status=STATUS_DRAFT,
        )
        db.add(assessment)
        db.flush()
        assessment_id = assessment.id
        print(f"Created Assessment id={assessment_id} (status=DRAFT).")

    for section_plan in plan.sections:
        if not section_plan.tasks:
            continue

        if section_plan.existing_id is not None:
            section_id = section_plan.existing_id
        else:
            section = AssessmentSection(
                assessment_id=assessment_id,
                skill=section_plan.skill,
                title=SECTION_TITLES[section_plan.skill],
                sort_order=1,
            )
            db.add(section)
            db.flush()
            section_id = section.id
            print(f"[{section_plan.skill}] Created Section id={section_id}.")

        created = 0
        for task_plan in section_plan.tasks:
            if task_plan.already_exists:
                continue
            task = AssessmentTask(
                section_id=section_id,
                task_type=task_plan.task_type,
                title=task_plan.title,
                instructions=task_plan.instructions,
                content=task_plan.content,
                sort_order=task_plan.sort_order,
                status=STATUS_PUBLISHED if task_plan.publish else STATUS_DRAFT,
                min_words=task_plan.min_words,
                max_words=task_plan.max_words,
                prep_seconds=task_plan.prep_seconds,
                speak_seconds=task_plan.speak_seconds,
                evaluation_mode=task_plan.evaluation_mode,
            )
            db.add(task)
            created += 1
        if created:
            print(f"[{section_plan.skill}] Created {created} task(s).")

    db.commit()
    print()
    print("Done. Committed.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read-only: print the migration plan, write nothing to the database.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        lesson = find_lesson_1(db)
        if lesson is None:
            print(
                "ERROR: could not find an existing A1 Lesson 1 "
                "(Language 'de' -> Course level='A1' -> first Module -> Lesson number=1). "
                "Nothing to migrate - aborting without changes."
            )
            return

        plan = build_plan(db, lesson)

        if args.dry_run:
            print("=== DRY RUN - no database writes will be made ===\n")
            print_plan(plan)
            return

        print_plan(plan)
        print()
        if plan.to_create_count() == 0:
            print("Nothing to create - already migrated. No changes made.")
            return
        apply_plan(db, plan)

    finally:
        db.close()


if __name__ == "__main__":
    main()
