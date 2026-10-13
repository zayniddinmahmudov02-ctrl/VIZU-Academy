"""VIZU LMS course structure: five CEFR levels with a fixed number of lessons.

A level is a `courses` row (language "de", level A1..C1). Its lessons live in
the level's main module — the first module by (order_index, number), the
same one the student sidebar shows — numbered 1..N. Nothing here deletes or
renumbers existing lessons except the explicit admin reorder."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.language import Language
from app.models.lesson import Lesson
from app.models.lms import COMPETENCY_ORDER, COMPETENCY_POSITION, LessonCompetency
from app.models.module import Module

LEVELS: tuple[str, ...] = ("A1", "A2", "B1", "B2", "C1")
LEVEL_LESSON_COUNTS: dict[str, int] = {"A1": 14, "A2": 14, "B1": 20, "B2": 30, "C1": 22}
TOTAL_LESSONS = sum(LEVEL_LESSON_COUNTS.values())
LANGUAGE_CODE = "de"


def normalize_level(level: str) -> str:
    code = (level or "").strip().upper()
    if code not in LEVEL_LESSON_COUNTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UNKNOWN_LEVEL")
    return code


def level_course(db: Session, level: str) -> Course | None:
    return db.scalar(
        select(Course)
        .join(Language, Language.id == Course.language_id)
        .where(Language.code == LANGUAGE_CODE, Course.level == level)
        .order_by(Course.order_index, Course.created_at)
        .limit(1)
    )


def main_module(db: Session, course: Course) -> Module | None:
    return db.scalar(
        select(Module).where(Module.course_id == course.id).order_by(Module.order_index, Module.number, Module.created_at).limit(1)
    )


def level_lessons(db: Session, module: Module | None, published_only: bool = False) -> list[Lesson]:
    if module is None:
        return []
    q = select(Lesson).where(Lesson.module_id == module.id)
    if published_only:
        q = q.where(Lesson.is_published.is_(True))
    return list(db.scalars(q.order_by(Lesson.number)))


def lesson_level(db: Session, lesson: Lesson) -> tuple[Course | None, Module | None]:
    module = db.get(Module, lesson.module_id)
    course = db.get(Course, module.course_id) if module else None
    return course, module


def ensure_competencies(db: Session, lesson: Lesson, published: bool = False) -> list[LessonCompetency]:
    """The ten competency rows of a lesson, creating missing ones (new rows
    are drafts unless `published`). Never changes existing rows."""
    rows = {c.kind: c for c in db.scalars(select(LessonCompetency).where(LessonCompetency.lesson_id == lesson.id))}
    for kind in COMPETENCY_ORDER:
        if kind not in rows:
            rows[kind] = LessonCompetency(lesson_id=lesson.id, kind=kind, position=COMPETENCY_POSITION[kind], is_published=published)
            db.add(rows[kind])
    return [rows[k] for k in COMPETENCY_ORDER]


def ensure_structure(db: Session, level: str) -> dict:
    """Course, main module and lessons 1..N (missing ones as drafts titled
    "Lektion N") plus each lesson's competency rows. Idempotent; reports what
    it created. Lessons outside 1..N are left alone and reported."""
    level = normalize_level(level)
    created = {"course": False, "module": False, "lessons": [], "competencies": 0}
    language = db.scalar(select(Language).where(Language.code == LANGUAGE_CODE))
    if language is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="LANGUAGE_DE_MISSING")
    course = level_course(db, level)
    if course is None:
        course = Course(language_id=language.id, level=level, title=f"VIZU-DEUTSCH {level}", order_index=LEVELS.index(level) + 1, is_active=True)
        db.add(course)
        db.flush()
        created["course"] = True
    module = main_module(db, course)
    if module is None:
        module = Module(course_id=course.id, number=1, title=f"VIZU-DEUTSCH {level}", order_index=1, is_active=True)
        db.add(module)
        db.flush()
        created["module"] = True
    existing = {lesson.number: lesson for lesson in level_lessons(db, module)}
    for number in range(1, LEVEL_LESSON_COUNTS[level] + 1):
        lesson = existing.get(number)
        if lesson is None:
            lesson = Lesson(module_id=module.id, number=number, title=f"Lektion {number}", duration=0, is_free=False, is_published=False)
            db.add(lesson)
            db.flush()
            created["lessons"].append(number)
        before = db.scalar(select(LessonCompetency.id).where(LessonCompetency.lesson_id == lesson.id).limit(1))
        if before is None:
            # brand-new lessons get draft competencies; an existing lesson
            # without rows (created outside the LMS) keeps showing content
            ensure_competencies(db, lesson, published=number not in created["lessons"])
            created["competencies"] += len(COMPETENCY_ORDER)
    db.commit()
    outside = sorted(n for n in existing if not 1 <= n <= LEVEL_LESSON_COUNTS[level])
    return {"level": level, "course_id": course.id, "module_id": module.id, "created": created, "numbers_outside_range": outside}


def validate_lesson_number(db: Session, lesson: Lesson, number: int) -> None:
    course, module = lesson_level(db, lesson)
    if course is None or course.level not in LEVEL_LESSON_COUNTS:
        return
    if not 1 <= number <= LEVEL_LESSON_COUNTS[course.level]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"LESSON_NUMBER_OUT_OF_RANGE: 1-{LEVEL_LESSON_COUNTS[course.level]}")
    clash = db.scalar(select(Lesson.id).where(Lesson.module_id == lesson.module_id, Lesson.number == number, Lesson.id != lesson.id))
    if clash is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="LESSON_NUMBER_TAKEN")


def reorder(db: Session, level: str, lesson_ids: list[UUID]) -> list[Lesson]:
    """Renumber the level's main-module lessons 1..N in the given order. The
    list must contain exactly the module's lessons. Two-phase update so the
    UNIQUE(module_id, number) index never sees a transient duplicate."""
    level = normalize_level(level)
    course = level_course(db, level)
    module = main_module(db, course) if course else None
    lessons = level_lessons(db, module)
    by_id = {lesson.id: lesson for lesson in lessons}
    if len(lesson_ids) != len(set(lesson_ids)) or set(lesson_ids) != set(by_id):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="REORDER_MUST_LIST_EVERY_LESSON_ONCE")
    if len(lesson_ids) > LEVEL_LESSON_COUNTS[level]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="TOO_MANY_LESSONS_FOR_LEVEL")
    for i, lesson_id in enumerate(lesson_ids, start=1):
        by_id[lesson_id].number = -i
    db.flush()
    for lesson in by_id.values():
        lesson.number = -lesson.number
    db.commit()
    return level_lessons(db, module)
