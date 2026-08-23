from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.assessment_section import AssessmentSection
from app.models.assessment_task import AssessmentTask
from app.models.grammar import Grammar
from app.models.lesson import Lesson
from app.models.listening import Listening
from app.models.quiz import QUIZ_TYPE_GRAMMAR, QUIZ_TYPE_LESSON, Quiz
from app.models.student_progress import StudentProgress
from app.models.user import User
from app.models.video import Video
from app.models.vocabulary import Vocabulary

from app.repositories.lesson import LessonRepository
from app.schemas.lesson import LessonCreate, LessonUpdate
from app.services.vizu_pay.access import can_access_lesson, is_free_lesson


class LessonService:
    """Admin CRUD for lessons — separate from the plain-function reads
    above (`get_all_lessons`/`get_lesson_detail`), which serve the
    student-facing shape (`LessonListItem`/`LessonDetail`, progress-aware)
    that this class has no reason to duplicate."""

    def __init__(self, db: Session):
        self.repository = LessonRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, lesson_id: str):
        return self.repository.get(lesson_id)

    def get_by_module(self, module_id: str):
        return self.repository.get_by_module(module_id)

    def create(self, data: LessonCreate):
        return self.repository.create(data)

    def update(self, lesson_id: str, data: LessonUpdate):
        lesson = self.repository.get(lesson_id)

        if not lesson:
            return None

        return self.repository.update(lesson, data)

    def delete(self, lesson_id: str):
        lesson = self.repository.get(lesson_id)

        if not lesson:
            return False

        self.repository.delete(lesson)

        return True


def _progress_percent(progress: StudentProgress | None) -> int:
    return 100 if (progress is not None and progress.lesson_completed) else 0


def get_content_status_for_module(db: Session, module_id: str) -> list[dict]:
    """Admin-facing — real per-panel content status (Video/Grammatik/Lesen/
    Hören/Schreiben/Sprechen/Wortschatz) for every lesson in a module, in a
    fixed small number of batched queries rather than one round-trip per
    lesson per panel (avoids N+1 on a level with e.g. 30 lessons). "Has
    content" here means any row exists, draft included — this is the
    admin's own "did I add something yet" view, not the public
    published-only gate."""
    lesson_ids = [
        row[0] for row in db.execute(select(Lesson.id).where(Lesson.module_id == module_id)).all()
    ]
    if not lesson_ids:
        return []

    def _lesson_ids_with(model) -> set:
        # Stringified unconditionally — every one of these lesson_id
        # columns (Video/Vocabulary/Grammar, and Quiz.lesson_id below)
        # resolves to a native UUID(as_uuid=True) column at the DB level
        # regardless of a `Mapped[str]` vs `Mapped[UUID]` Python
        # annotation (mapped_column(ForeignKey(...)) with no explicit
        # type infers from the FK target, Lesson.id — confirmed via
        # Quiz.__table__.columns["lesson_id"].type.python_type). str() on
        # an already-str value is a no-op, so this is safe either way —
        # what matters is every lookup below uses the same str(...) key.
        return {
            str(row[0])
            for row in db.execute(
                select(model.lesson_id).where(model.lesson_id.in_(lesson_ids)).distinct()
            ).all()
        }

    video_lessons = _lesson_ids_with(Video)
    grammar_lessons = _lesson_ids_with(Grammar)
    vocabulary_lessons = _lesson_ids_with(Vocabulary)

    skill_rows = db.execute(
        select(Assessment.lesson_id, AssessmentSection.skill)
        .join(AssessmentSection, AssessmentSection.assessment_id == Assessment.id)
        .join(AssessmentTask, AssessmentTask.section_id == AssessmentSection.id)
        .where(Assessment.lesson_id.in_(lesson_ids))
        .distinct()
    ).all()
    skills_by_lesson: dict = {}
    for lesson_id, skill in skill_rows:
        skills_by_lesson.setdefault(lesson_id, set()).add(skill)

    quiz_type_rows = db.execute(
        select(Quiz.lesson_id, Quiz.quiz_type)
        .where(Quiz.lesson_id.in_(lesson_ids), Quiz.is_published.is_(True))
        .distinct()
    ).all()
    quiz_types_by_lesson: dict = {}
    for lesson_id, quiz_type in quiz_type_rows:
        # Quiz.lesson_id is declared `Mapped[str]` in the ORM, but
        # mapped_column(ForeignKey("lessons.id")) with no explicit type
        # infers the actual column type from the FK target (Lesson.id,
        # UUID(as_uuid=True)) — confirmed directly via
        # Quiz.__table__.columns["lesson_id"].type.python_type, which is
        # uuid.UUID, not str. So `lesson_id` here is a real UUID object,
        # not a string, even though the annotation suggests otherwise —
        # stringify it so it actually matches the str(lesson.id) lookups
        # below (has_grammar_quiz/has_lesson_quiz), which a bare
        # `lesson_id` key never did (a UUID object and its str() are
        # different dict keys).
        quiz_types_by_lesson.setdefault(str(lesson_id), set()).add(quiz_type)

    lessons = db.scalars(
        select(Lesson).where(Lesson.module_id == module_id).order_by(Lesson.number)
    ).all()

    return [
        {
            "lesson_id": str(lesson.id),
            "number": lesson.number,
            "title": lesson.title,
            "has_video": str(lesson.id) in video_lessons,
            "has_grammar": str(lesson.id) in grammar_lessons,
            "has_grammar_quiz": QUIZ_TYPE_GRAMMAR in quiz_types_by_lesson.get(str(lesson.id), set()),
            "has_vocabulary": str(lesson.id) in vocabulary_lessons,
            # Lesen/Hören each unify passage + comprehension questions
            # into one Assessment-engine section — "Lesen" and "Lesen
            # Quiz" are the same underlying content, shown as two rows.
            "has_lesen": "LESEN" in skills_by_lesson.get(lesson.id, set()),
            "has_lesen_quiz": "LESEN" in skills_by_lesson.get(lesson.id, set()),
            "has_hoeren": "HOEREN" in skills_by_lesson.get(lesson.id, set()),
            "has_hoeren_quiz": "HOEREN" in skills_by_lesson.get(lesson.id, set()),
            "has_schreiben": "SCHREIBEN" in skills_by_lesson.get(lesson.id, set()),
            "has_sprechen": "SPRECHEN" in skills_by_lesson.get(lesson.id, set()),
            "has_lesson_quiz": QUIZ_TYPE_LESSON in quiz_types_by_lesson.get(str(lesson.id), set()),
            # Position-based only — "would a free student be locked out",
            # not "is this admin locked out" (admins always bypass).
            "is_locked": not is_free_lesson(lesson),
        }
        for lesson in lessons
    ]


def get_lessons_for_module(db: Session, module_id: str, user: User | None = None) -> list[dict]:
    """Public listing — every lesson stays visible regardless of lock
    state (per-lesson `is_locked`/`requires_premium` only), so the
    course structure is always browsable. Premium status for `user` is
    resolved once by the caller, not per lesson — avoids an N+1 query
    across e.g. 30 lessons in a level."""
    lessons = db.scalars(
        select(Lesson)
        .where(Lesson.module_id == module_id)
        .order_by(Lesson.number)
    ).all()

    return [_serialize_lesson_response(lesson, user) for lesson in lessons]


def _serialize_lesson_response(lesson: Lesson, user: User | None) -> dict:
    locked = not can_access_lesson(user, lesson)
    return {
        "id": lesson.id,
        "module_id": lesson.module_id,
        "number": lesson.number,
        "title": lesson.title,
        "duration": lesson.duration,
        "video_url": lesson.video_url,
        "is_free": lesson.is_free,
        "is_locked": locked,
        "requires_premium": locked,
    }


def get_all_lessons(db: Session, user: User) -> list[dict]:
    lessons = db.scalars(
        select(Lesson).order_by(Lesson.number)
    ).all()

    progress_by_lesson = {
        row.lesson_id: row
        for row in db.scalars(
            select(StudentProgress).where(StudentProgress.user_id == user.id)
        ).all()
    }

    return [
        {
            "id": str(lesson.id),
            "module_id": str(lesson.module_id),
            "number": lesson.number,
            "title": lesson.title,
            "duration": lesson.duration,
            "video_url": lesson.video_url,
            "is_free": lesson.is_free,
            "progress": _progress_percent(progress_by_lesson.get(lesson.id)),
            "is_locked": not can_access_lesson(user, lesson),
            "requires_premium": not can_access_lesson(user, lesson),
        }
        for lesson in lessons
    ]


def get_lesson_detail(db: Session, lesson_id: str, user_id: str) -> dict | None:
    """Access is already enforced upstream by the require_lesson_access
    dependency on the router — by the time this runs, the caller is
    known to have access, so is_locked/requires_premium are always False
    here (still included for schema consistency)."""
    lesson = db.get(Lesson, UUID(lesson_id))

    if lesson is None:
        return None

    listening = db.scalars(
        select(Listening)
        .where(
            Listening.lesson_id == lesson.id,
            Listening.is_published.is_(True),
        )
        .order_by(Listening.order_index)
        .limit(1)
    ).first()

    progress = db.scalars(
        select(StudentProgress).where(
            StudentProgress.user_id == user_id,
            StudentProgress.lesson_id == lesson.id,
        )
    ).first()

    return {
        "id": str(lesson.id),
        "module_id": str(lesson.module_id),
        "number": lesson.number,
        "title": lesson.title,
        "duration": lesson.duration,
        "video_url": lesson.video_url,
        "audio_url": listening.audio_url if listening else None,
        "is_free": lesson.is_free,
        "progress": _progress_percent(progress),
        "is_locked": False,
        "requires_premium": not is_free_lesson(lesson),
    }
