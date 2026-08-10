from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.assessment import Assessment, STATUS_PUBLISHED, TYPE_COURSE
from app.models.assessment_section import AssessmentSection
from app.models.assessment_task import AssessmentTask
from app.models.task_question import TaskQuestion

from app.schemas.assessment_engine import (
    PublicAssessment,
    PublicAssessmentSection,
    PublicAssessmentTask,
    PublicTaskOption,
    PublicTaskQuestion,
    PublicWritingRubricCriterion,
)


def _with_full_load(query):
    return query.options(
        selectinload(Assessment.sections)
        .selectinload(AssessmentSection.tasks)
        .selectinload(AssessmentTask.questions)
        .selectinload(TaskQuestion.options),
        selectinload(Assessment.sections).selectinload(AssessmentSection.tasks).selectinload(AssessmentTask.audio),
        selectinload(Assessment.sections)
        .selectinload(AssessmentSection.tasks)
        .selectinload(AssessmentTask.rubric_criteria),
    )


def get_published_assessment(db: Session, assessment_id: str) -> Assessment | None:
    """Only ever returns a PUBLISHED assessment — DRAFT/ARCHIVED are
    invisible to this function by construction, not by a caller-side
    check, so no route can accidentally leak unpublished content."""
    query = _with_full_load(
        select(Assessment).where(
            Assessment.id == UUID(assessment_id),
            Assessment.status == STATUS_PUBLISHED,
        )
    )
    return db.scalars(query).first()


def get_published_assessment_for_lesson(db: Session, lesson_id: str) -> Assessment | None:
    """The public Course/Lesson page's entry point — returns the PUBLISHED
    COURSE-type assessment for this lesson, or None (empty state, never a
    fabricated placeholder) if the admin hasn't published one yet."""
    query = _with_full_load(
        select(Assessment).where(
            Assessment.lesson_id == UUID(lesson_id),
            Assessment.assessment_type == TYPE_COURSE,
            Assessment.status == STATUS_PUBLISHED,
        )
    )
    return db.scalars(query).first()


def to_public_schema(assessment: Assessment) -> PublicAssessment:
    """Strips every correct-answer field (TaskOption.is_correct/
    match_value, TaskQuestion.correct_text_answer/alternative_answers/
    case_sensitive) — the public/student-facing shape can never carry
    them, regardless of what the admin API returns."""
    return PublicAssessment(
        id=str(assessment.id),
        title=assessment.title,
        description=assessment.description,
        allow_edit=assessment.allow_edit,
        allow_resubmit=assessment.allow_resubmit,
        sections=[
            PublicAssessmentSection(
                id=str(section.id),
                skill=section.skill,
                title=section.title,
                instructions=section.instructions,
                sort_order=section.sort_order,
                tasks=[
                    PublicAssessmentTask(
                        id=str(task.id),
                        task_type=task.task_type,
                        title=task.title,
                        instructions=task.instructions,
                        content=task.content,
                        config=task.config,
                        max_points=task.max_points,
                        sort_order=task.sort_order,
                        has_audio=task.audio is not None,
                        audio_duration_seconds=task.audio.duration_seconds if task.audio else None,
                        audio_play_limit=task.audio_play_limit,
                        allow_pause=task.allow_pause,
                        allow_seek=task.allow_seek,
                        allow_replay=task.allow_replay,
                        allow_speed_change=task.allow_speed_change,
                        image_url=task.image_url,
                        min_words=task.min_words,
                        max_words=task.max_words,
                        time_limit_minutes=task.time_limit_minutes,
                        prep_seconds=task.prep_seconds,
                        speak_seconds=task.speak_seconds,
                        rubric_criteria=[
                            PublicWritingRubricCriterion(
                                id=str(c.id), name=c.name, max_score=c.max_score, sort_order=c.sort_order
                            )
                            for c in sorted(task.rubric_criteria, key=lambda c: c.sort_order)
                        ],
                        questions=[
                            PublicTaskQuestion(
                                id=str(question.id),
                                prompt=question.prompt,
                                points=question.points,
                                sort_order=question.sort_order,
                                options=[
                                    PublicTaskOption(
                                        id=str(option.id),
                                        option_text=option.option_text,
                                        sort_order=option.sort_order,
                                    )
                                    for option in sorted(question.options, key=lambda o: o.sort_order)
                                ],
                            )
                            for question in sorted(task.questions, key=lambda q: q.sort_order)
                        ],
                    )
                    for task in sorted(section.tasks, key=lambda t: t.sort_order)
                ],
            )
            for section in sorted(assessment.sections, key=lambda s: s.sort_order)
        ],
    )
