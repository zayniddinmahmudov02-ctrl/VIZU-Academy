from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.assessment import TYPE_MOCK_TEST, Assessment
from app.models.assessment_section import AssessmentSection
from app.models.assessment_task import TYPE_SPEAKING, TYPE_WRITING, AssessmentTask
from app.models.speaking_submission import SpeakingSubmission
from app.models.task_audio import TaskAudio
from app.models.task_option import TaskOption
from app.models.task_question import TaskQuestion
from app.models.user import User
from app.models.writing_rubric_criterion import WritingRubricCriterion

from app.schemas.assessment_engine import (
    AssessmentCreate,
    AssessmentSectionCreate,
    AssessmentSectionUpdate,
    AssessmentTaskCreate,
    AssessmentTaskUpdate,
    AssessmentUpdate,
    TaskOptionCreate,
    TaskOptionUpdate,
    TaskQuestionCreate,
    TaskQuestionUpdate,
    WritingRubricCriterionCreate,
    WritingRubricCriterionUpdate,
)

KOMPETENZ_TITLES = {
    "LESEN": "Lesen",
    "HOEREN": "Hören",
    "SCHREIBEN": "Schreiben",
    "SPRECHEN": "Sprechen",
}

from .audio_service import storage as audio_storage
from .scoring import get_handler


async def _delete_audio_files_for_tasks(db: Session, task_ids: list[UUID]) -> None:
    """Best-effort cleanup of on-disk audio files before their DB rows are
    cascade-deleted along with the parent task/section/assessment — the DB
    FK cascade removes the TaskAudio/SpeakingSubmission *rows* for free,
    but never touches the actual file on disk, so this has to happen
    explicitly first. Covers both admin-uploaded task audio (Hören) and
    student-submitted recordings (Sprechen) — same storage, same risk of
    an orphaned file otherwise."""
    if not task_ids:
        return
    audios = db.scalars(select(TaskAudio).where(TaskAudio.task_id.in_(task_ids))).all()
    submissions = db.scalars(select(SpeakingSubmission).where(SpeakingSubmission.task_id.in_(task_ids))).all()
    for audio in [*audios, *submissions]:
        try:
            await audio_storage.delete(audio.storage_path)
        except OSError:
            pass


# ============================================================
# Assessment
# ============================================================

def list_assessments(
    db: Session,
    assessment_type: str | None = None,
    status: str | None = None,
    lesson_id: str | None = None,
) -> list[Assessment]:
    query = select(Assessment).order_by(Assessment.created_at.desc())
    if assessment_type:
        query = query.where(Assessment.assessment_type == assessment_type)
    if status:
        query = query.where(Assessment.status == status)
    if lesson_id:
        query = query.where(Assessment.lesson_id == UUID(lesson_id))
    return list(db.scalars(query).all())


def get_assessment(db: Session, assessment_id: str) -> Assessment | None:
    return db.get(Assessment, UUID(assessment_id))


def get_assessment_with_sections(db: Session, assessment_id: str) -> Assessment | None:
    query = (
        select(Assessment)
        .where(Assessment.id == UUID(assessment_id))
        .options(
            selectinload(Assessment.sections)
            .selectinload(AssessmentSection.tasks)
            .selectinload(AssessmentTask.questions)
            .selectinload(TaskQuestion.options),
            selectinload(Assessment.sections).selectinload(AssessmentSection.tasks).selectinload(AssessmentTask.audio),
            selectinload(Assessment.sections)
            .selectinload(AssessmentSection.tasks)
            .selectinload(AssessmentTask.rubric_criteria),
        )
    )
    return db.scalars(query).first()


def create_assessment(db: Session, data: AssessmentCreate, actor: User) -> Assessment:
    if data.lesson_id and data.model_test_id:
        raise HTTPException(
            status_code=422,
            detail="An assessment belongs to at most one of lesson_id or model_test_id, not both.",
        )

    assessment = Assessment(
        **data.model_dump(),
        created_by_id=actor.id,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def get_or_create_model_test_kompetenz_section(
    db: Session, model_test_id: str, skill: str, actor: User
) -> AssessmentSection:
    """The ModelTest-side integration point: given a ModelTest and one of
    the four skill codes, returns the AssessmentSection that represents
    that Kompetenz — creating the wrapping MOCK_TEST Assessment and the
    Section itself on first use (mirrors the lazy-creation pattern already
    used for LanguageSettings), so the admin Task Manager never has to
    walk the admin through manually creating an Assessment first. Reuses
    whichever Assessment already exists for this ModelTest rather than
    creating a second one — one Assessment per ModelTest, one Section per
    skill within it."""
    assessment = db.scalar(
        select(Assessment).where(
            Assessment.model_test_id == UUID(model_test_id),
            Assessment.assessment_type == TYPE_MOCK_TEST,
        )
    )
    if assessment is None:
        assessment = Assessment(
            title="Modelltest Aufgaben",
            assessment_type=TYPE_MOCK_TEST,
            model_test_id=UUID(model_test_id),
            created_by_id=actor.id,
        )
        db.add(assessment)
        db.flush()

    section = db.scalar(
        select(AssessmentSection).where(
            AssessmentSection.assessment_id == assessment.id,
            AssessmentSection.skill == skill,
        )
    )
    if section is None:
        section = AssessmentSection(
            assessment_id=assessment.id,
            skill=skill,
            title=KOMPETENZ_TITLES.get(skill, skill),
            sort_order=1,
        )
        db.add(section)

    db.commit()
    db.refresh(section)
    return section


def get_or_create_lesson_kompetenz_section(
    db: Session, lesson_id: str, skill: str, actor: User
) -> AssessmentSection:
    """Course-side equivalent of get_or_create_model_test_kompetenz_section
    — same lazy-creation pattern, keyed on lesson_id (TYPE_COURSE) instead
    of model_test_id (TYPE_MOCK_TEST). One Assessment per Lesson, one
    Section per skill within it."""
    assessment = db.scalar(
        select(Assessment).where(
            Assessment.lesson_id == UUID(lesson_id),
            Assessment.assessment_type == "COURSE",
        )
    )
    if assessment is None:
        assessment = Assessment(
            title="Lektion Aufgaben",
            assessment_type="COURSE",
            lesson_id=UUID(lesson_id),
            created_by_id=actor.id,
        )
        db.add(assessment)
        db.flush()

    section = db.scalar(
        select(AssessmentSection).where(
            AssessmentSection.assessment_id == assessment.id,
            AssessmentSection.skill == skill,
        )
    )
    if section is None:
        section = AssessmentSection(
            assessment_id=assessment.id,
            skill=skill,
            title=KOMPETENZ_TITLES.get(skill, skill),
            sort_order=1,
        )
        db.add(section)

    db.commit()
    db.refresh(section)
    return section


def update_assessment(db: Session, assessment_id: str, data: AssessmentUpdate) -> Assessment | None:
    assessment = get_assessment(db, assessment_id)
    if assessment is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(assessment, key, value)
    db.commit()
    db.refresh(assessment)
    return assessment


async def delete_assessment(db: Session, assessment_id: str) -> bool:
    assessment = get_assessment(db, assessment_id)
    if assessment is None:
        return False

    task_ids = db.scalars(
        select(AssessmentTask.id)
        .join(AssessmentSection, AssessmentTask.section_id == AssessmentSection.id)
        .where(AssessmentSection.assessment_id == assessment.id)
    ).all()
    await _delete_audio_files_for_tasks(db, list(task_ids))

    db.delete(assessment)
    db.commit()
    return True


# ============================================================
# Section
# ============================================================

def list_sections(db: Session, assessment_id: str) -> list[AssessmentSection]:
    query = (
        select(AssessmentSection)
        .where(AssessmentSection.assessment_id == UUID(assessment_id))
        .order_by(AssessmentSection.sort_order)
    )
    return list(db.scalars(query).all())


def create_section(db: Session, data: AssessmentSectionCreate) -> AssessmentSection:
    section = AssessmentSection(**data.model_dump())
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


def update_section(db: Session, section_id: str, data: AssessmentSectionUpdate) -> AssessmentSection | None:
    section = db.get(AssessmentSection, UUID(section_id))
    if section is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(section, key, value)
    db.commit()
    db.refresh(section)
    return section


async def delete_section(db: Session, section_id: str) -> bool:
    section = db.get(AssessmentSection, UUID(section_id))
    if section is None:
        return False

    task_ids = db.scalars(select(AssessmentTask.id).where(AssessmentTask.section_id == section.id)).all()
    await _delete_audio_files_for_tasks(db, list(task_ids))

    db.delete(section)
    db.commit()
    return True


# ============================================================
# Task
# ============================================================

def list_tasks(db: Session, section_id: str) -> list[AssessmentTask]:
    query = (
        select(AssessmentTask)
        .where(AssessmentTask.section_id == UUID(section_id))
        .options(
            selectinload(AssessmentTask.questions).selectinload(TaskQuestion.options),
            selectinload(AssessmentTask.audio),
            selectinload(AssessmentTask.rubric_criteria),
        )
        .order_by(AssessmentTask.sort_order)
    )
    return list(db.scalars(query).all())


def get_task(db: Session, task_id: str) -> AssessmentTask | None:
    query = (
        select(AssessmentTask)
        .where(AssessmentTask.id == UUID(task_id))
        .options(
            selectinload(AssessmentTask.questions).selectinload(TaskQuestion.options),
            selectinload(AssessmentTask.audio),
            selectinload(AssessmentTask.rubric_criteria),
        )
    )
    return db.scalars(query).first()


def create_task(db: Session, data: AssessmentTaskCreate) -> AssessmentTask:
    task = AssessmentTask(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task_id: str, data: AssessmentTaskUpdate) -> AssessmentTask | None:
    task = db.get(AssessmentTask, UUID(task_id))
    if task is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return get_task(db, task_id)


async def delete_task(db: Session, task_id: str) -> bool:
    task = db.get(AssessmentTask, UUID(task_id))
    if task is None:
        return False

    await _delete_audio_files_for_tasks(db, [task.id])

    db.delete(task)
    db.commit()
    return True


def reorder_tasks(db: Session, section_id: str, ordered_task_ids: list[str]) -> list[AssessmentTask]:
    """Explicit reorder — sort_order is set from the given list's position,
    never inferred from insertion/created_at order. Only touches tasks that
    both belong to this section AND appear in the list; anything not
    included keeps its current sort_order rather than being silently
    reset."""
    tasks_by_id = {
        str(t.id): t
        for t in db.scalars(select(AssessmentTask).where(AssessmentTask.section_id == UUID(section_id))).all()
    }
    for index, task_id in enumerate(ordered_task_ids, start=1):
        task = tasks_by_id.get(task_id)
        if task is not None:
            task.sort_order = index
    db.commit()
    return list_tasks(db, section_id)


def validate_task(db: Session, task_id: str) -> list[str]:
    """Runs the task_type's handler.validate_task() against this task's
    current questions — the admin builder calls this before allowing a
    Publish. Unknown/unregistered task_type is itself an error rather than
    a crash. WRITING is scored by AI/teacher evaluation, not the objective
    TaskQuestion registry, so it's validated separately: publishable once
    it has at least one rubric criterion."""
    task = get_task(db, task_id)
    if task is None:
        return ["Task not found."]

    if task.task_type in (TYPE_WRITING, TYPE_SPEAKING):
        return [] if task.rubric_criteria else ["Task has no rubric criteria yet."]

    try:
        handler = get_handler(task.task_type)
    except ValueError as exc:
        return [str(exc)]
    if not task.questions:
        return ["Task has no questions yet."]
    return handler.validate_task(task.questions)


# ============================================================
# Task Question
# ============================================================

def _resync_task_max_points(db: Session, task_id: UUID) -> None:
    """AssessmentTask.max_points is a stored column (per spec: "every task
    has max_points"), but its correct value is always the sum of its
    questions' points — kept in sync here after every question mutation
    rather than trusting the admin to hand-edit two numbers in step."""
    task = db.get(AssessmentTask, task_id)
    if task is None:
        return
    total = db.scalar(
        select(func.coalesce(func.sum(TaskQuestion.points), 0)).where(TaskQuestion.task_id == task_id)
    )
    task.max_points = int(total)
    db.commit()


def create_question(db: Session, data: TaskQuestionCreate) -> TaskQuestion:
    question = TaskQuestion(**data.model_dump())
    db.add(question)
    db.commit()
    db.refresh(question)
    _resync_task_max_points(db, question.task_id)
    db.refresh(question)
    return question


def update_question(db: Session, question_id: str, data: TaskQuestionUpdate) -> TaskQuestion | None:
    question = db.get(TaskQuestion, UUID(question_id))
    if question is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(question, key, value)
    db.commit()
    if "points" in data.model_dump(exclude_unset=True):
        _resync_task_max_points(db, question.task_id)
    db.refresh(question)
    return question


def delete_question(db: Session, question_id: str) -> bool:
    question = db.get(TaskQuestion, UUID(question_id))
    if question is None:
        return False
    task_id = question.task_id
    db.delete(question)
    db.commit()
    _resync_task_max_points(db, task_id)
    return True


# ============================================================
# Task Option
# ============================================================

def create_option(db: Session, data: TaskOptionCreate) -> TaskOption:
    option = TaskOption(**data.model_dump())
    db.add(option)
    db.commit()
    db.refresh(option)
    return option


def update_option(db: Session, option_id: str, data: TaskOptionUpdate) -> TaskOption | None:
    option = db.get(TaskOption, UUID(option_id))
    if option is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(option, key, value)
    db.commit()
    db.refresh(option)
    return option


def delete_option(db: Session, option_id: str) -> bool:
    option = db.get(TaskOption, UUID(option_id))
    if option is None:
        return False
    db.delete(option)
    db.commit()
    return True


# ============================================================
# Writing rubric criteria (SCHREIBEN) — never hardcoded, admin-defined
# per task; AssessmentTask.max_points is kept in sync as their sum, same
# pattern as _resync_task_max_points() above for the objective task types.
# ============================================================

def _resync_writing_task_max_points(db: Session, task_id: UUID) -> None:
    task = db.get(AssessmentTask, task_id)
    if task is None:
        return
    total = db.scalar(
        select(func.coalesce(func.sum(WritingRubricCriterion.max_score), 0)).where(
            WritingRubricCriterion.task_id == task_id
        )
    )
    task.max_points = int(total)
    db.commit()


def create_rubric_criterion(db: Session, data: WritingRubricCriterionCreate) -> WritingRubricCriterion:
    criterion = WritingRubricCriterion(**data.model_dump())
    db.add(criterion)
    db.commit()
    db.refresh(criterion)
    _resync_writing_task_max_points(db, criterion.task_id)
    db.refresh(criterion)
    return criterion


def update_rubric_criterion(
    db: Session, criterion_id: str, data: WritingRubricCriterionUpdate
) -> WritingRubricCriterion | None:
    criterion = db.get(WritingRubricCriterion, UUID(criterion_id))
    if criterion is None:
        return None
    changed = data.model_dump(exclude_unset=True)
    for key, value in changed.items():
        setattr(criterion, key, value)
    db.commit()
    if "max_score" in changed:
        _resync_writing_task_max_points(db, criterion.task_id)
    db.refresh(criterion)
    return criterion


def delete_rubric_criterion(db: Session, criterion_id: str) -> bool:
    criterion = db.get(WritingRubricCriterion, UUID(criterion_id))
    if criterion is None:
        return False
    task_id = criterion.task_id
    db.delete(criterion)
    db.commit()
    _resync_writing_task_max_points(db, task_id)
    return True
