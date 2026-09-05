"""Review-first cleanup: removes the Assessment Engine Hören/Schreiben/
Sprechen sections+tasks that migrate_lesson_1_assessments.py created for
A1 Lesson 1, now that those three skills are LEGACY-backed again (see
backend/app/services/lesson_progress/section_gate.py's module
docstring) and that migrated content is an orphaned duplicate the
student frontend no longer reads at all.

Scope, deliberately narrow:
  - Lesson 1 only (LEVEL/LESSON_NUMBER below) — never touches any other
    lesson's Assessment Engine content.
  - HOEREN/SCHREIBEN/SPRECHEN sections only — LESEN is never touched:
    migrate_lesson_1_assessments.py never created any Lesen content (it
    only ever built hoeren_plan/schreiben_plan/sprechen_plan — see that
    script), so there is no known migration-created Lesen duplicate for
    this tool to clean up. If a genuine Lesen duplicate exists, it did
    not come from that script and this one will not identify or touch
    it.
  - Only tasks matching the migration's exact fingerprint (task_type +
    title, see MIGRATED_TASK_TITLES below) are candidates — an
    AssessmentSection/AssessmentTask this tool didn't verifiably create
    is never touched, even if it happens to share a skill with one that
    was.
  - The shared Assessment row itself (which also holds Lesen's real,
    wanted content) is NEVER deleted, regardless of what else is
    cleaned up under it.

Dependency safety — a migrated task is only ever a deletion CANDIDATE;
it's excluded (report only, never deleted) the moment ANY of these
exist for it, each meaning something real happened since the migration
that this tool must not discard:
  - TaskQuestion rows (an admin added real content to a Hören task)
  - TaskAudio (an admin uploaded real audio)
  - WritingRubricCriterion (an admin configured real grading)
  - TaskAttempt (a student's assessment attempt touched this task)
  - WritingSubmission / SpeakingSubmission (a student actually
    submitted work through it)
A section is only deleted once every one of its tasks was actually
deleted (never partially) — a section with any remaining task (whether
skipped as unsafe or just not a migration match) is left in place.

DRY-RUN BY DEFAULT. Real deletion requires the explicit --confirm flag
(dry-run is the safe default here, unlike migrate_lesson_1_assessments.
py's additive migration, because this tool deletes data):

    python -m app.scripts.cleanup_lesson_1_assessment_duplicates
    python -m app.scripts.cleanup_lesson_1_assessment_duplicates --dry-run
    python -m app.scripts.cleanup_lesson_1_assessment_duplicates --confirm

Real deletion runs inside one transaction (commit only at the very end;
any error rolls back everything — nothing partial is ever left behind).
"""

import argparse
from dataclasses import dataclass, field
from uuid import UUID

import app.models  # noqa: F401 — registers every model with Base before querying

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.assessment import TYPE_COURSE, Assessment
from app.models.assessment_section import SKILL_HOEREN, SKILL_SCHREIBEN, SKILL_SPRECHEN, AssessmentSection
from app.models.assessment_task import TYPE_MULTIPLE_CHOICE, TYPE_SPEAKING, TYPE_WRITING, AssessmentTask
from app.models.course import Course
from app.models.language import Language
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.speaking_submission import SpeakingSubmission
from app.models.task_attempt import TaskAttempt
from app.models.task_audio import TaskAudio
from app.models.task_question import TaskQuestion
from app.models.writing_rubric_criterion import WritingRubricCriterion
from app.models.writing_submission import WritingSubmission

LEVEL = "A1"
LESSON_NUMBER = 1

# Exact fingerprint of what migrate_lesson_1_assessments.py creates —
# see that script's QUIZ_TITLE-equivalent constants (LISTENING_TEXTS/
# WRITING_TASKS/the single Sprechen task's title). Only a task matching
# BOTH task_type and title here is ever a candidate.
MIGRATED_TASK_TITLES = {
    (SKILL_HOEREN, TYPE_MULTIPLE_CHOICE): {"Text 1", "Text 2", "Text 3"},
    (SKILL_SCHREIBEN, TYPE_WRITING): {"Topshiriq 1", "Topshiriq 2", "Topshiriq 3", "Topshiriq 4"},
    (SKILL_SPRECHEN, TYPE_SPEAKING): {"Stellen Sie sich vor!"},
}
TARGET_SKILLS = (SKILL_HOEREN, SKILL_SCHREIBEN, SKILL_SPRECHEN)


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


@dataclass
class TaskFinding:
    task_id: UUID
    title: str
    task_type: str
    blockers: list[str] = field(default_factory=list)

    @property
    def safe_to_delete(self) -> bool:
        return not self.blockers


@dataclass
class SectionFinding:
    section_id: UUID
    skill: str
    tasks: list[TaskFinding] = field(default_factory=list)

    @property
    def all_tasks_safe(self) -> bool:
        return bool(self.tasks) and all(t.safe_to_delete for t in self.tasks)


@dataclass
class CleanupPlan:
    lesson_id: UUID
    assessment_id: UUID | None
    sections: list[SectionFinding] = field(default_factory=list)

    def safe_task_count(self) -> int:
        return sum(1 for s in self.sections for t in s.tasks if t.safe_to_delete)

    def unsafe_task_count(self) -> int:
        return sum(1 for s in self.sections for t in s.tasks if not t.safe_to_delete)

    def sections_fully_removable(self) -> list["SectionFinding"]:
        return [s for s in self.sections if s.all_tasks_safe]


def _dependency_blockers(db, task: AssessmentTask) -> list[str]:
    blockers = []
    if db.query(TaskQuestion.id).filter(TaskQuestion.task_id == task.id).first() is not None:
        blockers.append("has TaskQuestion rows (real content added since migration)")
    if db.query(TaskAudio.id).filter(TaskAudio.task_id == task.id).first() is not None:
        blockers.append("has a TaskAudio row (real audio uploaded since migration)")
    if db.query(WritingRubricCriterion.id).filter(WritingRubricCriterion.task_id == task.id).first() is not None:
        blockers.append("has WritingRubricCriterion rows (admin configured real grading)")
    if db.query(TaskAttempt.id).filter(TaskAttempt.task_id == task.id).first() is not None:
        blockers.append("has TaskAttempt rows (a student's attempt touched this task)")
    if db.query(WritingSubmission.id).filter(WritingSubmission.task_id == task.id).first() is not None:
        blockers.append("has WritingSubmission rows (a student submitted real work)")
    if db.query(SpeakingSubmission.id).filter(SpeakingSubmission.task_id == task.id).first() is not None:
        blockers.append("has SpeakingSubmission rows (a student submitted real work)")
    return blockers


def build_plan(db, lesson) -> CleanupPlan | None:
    assessments = db.scalars(
        select(Assessment).where(Assessment.lesson_id == lesson.id, Assessment.assessment_type == TYPE_COURSE)
    ).all()
    if not assessments:
        return None

    # migrate_lesson_1_assessments.py always reuses a single existing
    # Assessment (or creates exactly one if none existed) — scanning
    # every COURSE assessment for this lesson, not just one, is the
    # conservative choice: a duplicate Assessment (unrelated to this
    # tool) could in principle also carry a migrated-looking section.
    plan = CleanupPlan(lesson_id=lesson.id, assessment_id=assessments[0].id if len(assessments) == 1 else None)

    for assessment in assessments:
        sections = db.scalars(
            select(AssessmentSection).where(
                AssessmentSection.assessment_id == assessment.id,
                AssessmentSection.skill.in_(TARGET_SKILLS),
            )
        ).all()
        for section in sections:
            tasks = db.scalars(select(AssessmentTask).where(AssessmentTask.section_id == section.id)).all()
            finding = SectionFinding(section_id=section.id, skill=section.skill)
            for task in tasks:
                expected_titles = MIGRATED_TASK_TITLES.get((section.skill, task.task_type), set())
                if task.title not in expected_titles:
                    continue  # not a migration fingerprint match — never a candidate
                finding.tasks.append(
                    TaskFinding(
                        task_id=task.id,
                        title=task.title,
                        task_type=task.task_type,
                        blockers=_dependency_blockers(db, task),
                    )
                )
            if finding.tasks:
                plan.sections.append(finding)

    return plan


def print_plan(plan: CleanupPlan | None) -> None:
    if plan is None:
        print("No COURSE Assessment exists for this lesson at all - nothing to clean up.")
        return

    print(f"Lesson id: {plan.lesson_id}")
    if plan.assessment_id:
        print(f"Assessment id: {plan.assessment_id} (single COURSE assessment found for this lesson)")
    else:
        print("Multiple COURSE assessments found for this lesson - scanned all of them.")
    if not plan.sections:
        print("No migration-fingerprint-matching Hoeren/Schreiben/Sprechen tasks found - nothing to clean up.")
        return

    for section in plan.sections:
        print(f"\n[{section.skill}] Section id={section.section_id}")
        for task in section.tasks:
            if task.safe_to_delete:
                print(f"    SAFE TO DELETE  id={task.task_id} title={task.title!r} task_type={task.task_type}")
            else:
                print(f"    UNSAFE - SKIP   id={task.task_id} title={task.title!r} task_type={task.task_type}")
                for blocker in task.blockers:
                    print(f"        - {blocker}")
        if section.all_tasks_safe:
            print(f"    -> section would also be deleted (empty after its {len(section.tasks)} task(s) removed)")
        else:
            print("    -> section is kept (at least one unsafe/unmatched task remains)")

    print()
    print(f"Total safe-to-delete tasks: {plan.safe_task_count()}")
    print(f"Total unsafe (skipped) tasks: {plan.unsafe_task_count()}")
    print(f"Sections that would be fully removed: {len(plan.sections_fully_removable())}")
    if plan.unsafe_task_count():
        print(
            "NOTE: unsafe tasks are never deleted by this tool. Review them manually - "
            "real student/admin work exists on top of what the migration created."
        )


def apply_cleanup(db, plan: CleanupPlan) -> None:
    deleted_tasks = 0
    deleted_sections = 0
    for section in plan.sections:
        safe_tasks = [t for t in section.tasks if t.safe_to_delete]
        if len(safe_tasks) != len(section.tasks):
            print(f"[{section.skill}] Skipping section {section.section_id} - not all tasks are safe to delete.")
            continue
        for task_finding in safe_tasks:
            task = db.get(AssessmentTask, task_finding.task_id)
            if task is not None:
                db.delete(task)
                deleted_tasks += 1
        db.flush()
        section_obj = db.get(AssessmentSection, section.section_id)
        if section_obj is not None:
            db.delete(section_obj)
            deleted_sections += 1

    db.commit()
    print(f"Deleted {deleted_tasks} task(s) and {deleted_sections} section(s). Committed.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Explicit no-op flag — this is also the default.")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required to actually delete anything. Without it, the script always behaves as --dry-run.",
    )
    args = parser.parse_args()
    real_run = args.confirm and not args.dry_run

    db = SessionLocal()
    try:
        lesson = find_lesson_1(db)
        if lesson is None:
            print(
                "ERROR: could not find an existing A1 Lesson 1 "
                "(Language 'de' -> Course level='A1' -> first Module -> Lesson number=1). "
                "Nothing to clean up - aborting without changes."
            )
            return

        plan = build_plan(db, lesson)

        if not real_run:
            print("=== DRY RUN (default) - no database writes will be made ===\n")
            print_plan(plan)
            if not args.confirm:
                print("\nPass --confirm (without --dry-run) to actually delete the safe-to-delete rows above.")
            return

        print_plan(plan)
        print()
        if plan is None or plan.safe_task_count() == 0:
            print("Nothing safe to delete. No changes made.")
            return
        apply_cleanup(db, plan)

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
