"""Exercise sets of a lesson — Grammatik practice, Wortschatz practice and the
Yakuniy Test (skill_exercises). Same question types, the same public view
(no key) and the same server-side grading as Lesen / Hören; one attempt
history per exercise set.

Plus the lesson's Grammatik rules (grammars) and Wortschatz words
(vocabularies) for the admin editor."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.utils.safe_html import sanitize_html
from app.models.grammar import Grammar
from app.models.lesson_skill import (
    CONFIG_TYPES,
    EXERCISE_SKILLS,
    EXERCISE_SOURCE_BOOK,
    EXERCISE_SOURCE_VIZU,
    SkillExercise,
    SkillExerciseOption,
    SkillExerciseQuestion,
)
from app.models.vocabulary import Vocabulary
from app.services.lesson_skills import admin as skill_admin
from app.services.lesson_skills import skill_tests as tests

# URL segment <-> skill
SKILL_BY_SLUG = {"grammatik": "GRAMMATIK", "wortschatz": "WORTSCHATZ", "yakuniy": "YAKUNIY"}
SLUG_BY_SKILL = {v: k for k, v in SKILL_BY_SLUG.items()}


def skill_from_slug(slug: str) -> str:
    skill = SKILL_BY_SLUG.get((slug or "").strip().lower())
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown exercise skill.")
    return skill


def sorted_questions(exercise: SkillExercise) -> list[SkillExerciseQuestion]:
    return sorted(exercise.questions, key=lambda q: (q.order_index, q.created_at))


def has_key(question) -> bool:
    """A question can be graded only with a complete answer key."""
    if question.question_type in CONFIG_TYPES:
        # an imported Lückentext / Zuordnung may wait for its key ("pending")
        return bool(question.config) and not question.config.get("pending")
    return sum(1 for o in question.options if o.is_correct) == 1


# ============================================================
# Student
# ============================================================


def published_exercises(db: Session, lesson_id: UUID, skill: str) -> list[SkillExercise]:
    return list(
        db.scalars(
            select(SkillExercise)
            .where(SkillExercise.lesson_id == lesson_id, SkillExercise.skill == skill, SkillExercise.is_published.is_(True))
            .order_by(SkillExercise.order_index, SkillExercise.created_at)
        )
    )


def published_exercise(db: Session, lesson_id: UUID, skill: str, exercise_id: UUID) -> SkillExercise:
    ex = db.get(SkillExercise, exercise_id)
    if ex is None or str(ex.lesson_id) != str(lesson_id) or ex.skill != skill or not ex.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found.")
    return ex


def student_view(db: Session, user_id: UUID, lesson_id: UUID, skill: str) -> dict:
    out = []
    for ex in published_exercises(db, lesson_id, skill):
        questions = [q for q in sorted_questions(ex) if has_key(q)]
        if not questions:
            continue
        rows = tests.attempts(db, user_id, lesson_id, skill, exercise_id=ex.id)
        out.append(
            {
                "id": ex.id,
                "title": ex.title,
                "instruction": ex.instruction,
                "source": ex.source,
                "questions": [tests.public_question(q) for q in questions],
                "summary": tests.summary(rows),
                "attempts": [tests.attempt_item(a) for a in rows],
            }
        )
    return {"lesson_id": lesson_id, "skill": SLUG_BY_SKILL[skill], "exercises": out}


def gradable_questions(ex: SkillExercise) -> list:
    return [q for q in sorted_questions(ex) if has_key(q)]


# ============================================================
# Admin
# ============================================================


def admin_exercise(ex: SkillExercise) -> dict:
    questions = sorted_questions(ex)
    return {
        "id": ex.id,
        "lesson_id": ex.lesson_id,
        "skill": ex.skill,
        "title": ex.title,
        "instruction": ex.instruction,
        "order_index": ex.order_index,
        "is_published": ex.is_published,
        "source": ex.source,
        "content_id": ex.content_id,
        "question_count": len(questions),
        "max_points": sum(q.points for q in questions),
        "questions": [skill_admin.admin_question(q) for q in questions],
    }


def lesson_exercises(db: Session, lesson_id: UUID, skill: str | None = None) -> list[SkillExercise]:
    query = select(SkillExercise).where(SkillExercise.lesson_id == lesson_id)
    if skill:
        query = query.where(SkillExercise.skill == skill)
    return list(db.scalars(query.order_by(SkillExercise.skill, SkillExercise.order_index, SkillExercise.created_at)))


def _clean_meta(data: dict) -> dict:
    title = str(data.get("title") or "").strip()
    if not title or len(title) > 255:
        raise HTTPException(status_code=422, detail="Title is required (max 255 characters).")
    source = data.get("source") or EXERCISE_SOURCE_BOOK
    if source not in (EXERCISE_SOURCE_BOOK, EXERCISE_SOURCE_VIZU):
        raise HTTPException(status_code=422, detail="Unknown source.")
    return {
        "title": title,
        "instruction": (str(data.get("instruction") or "").strip() or None),
        "order_index": int(data.get("order_index") or 1),
        "is_published": bool(data.get("is_published")),
        "source": source,
    }


def _check_publishable(ex: SkillExercise) -> None:
    questions = sorted_questions(ex)
    if not questions:
        raise HTTPException(status_code=422, detail="NO_QUESTIONS")
    if any(not has_key(q) for q in questions):
        raise HTTPException(status_code=422, detail="KEY_REQUIRED")


def create_exercise(db: Session, lesson_id: UUID, data: dict) -> SkillExercise:
    skill = data.get("skill")
    if skill not in EXERCISE_SKILLS:
        raise HTTPException(status_code=422, detail="Unknown skill.")
    meta = _clean_meta(data)
    if meta["is_published"]:
        raise HTTPException(status_code=422, detail="NO_QUESTIONS")
    if not data.get("order_index"):
        meta["order_index"] = int(
            db.scalar(select(func.max(SkillExercise.order_index)).where(SkillExercise.lesson_id == lesson_id, SkillExercise.skill == skill)) or 0
        ) + 1
    ex = SkillExercise(lesson_id=lesson_id, skill=skill, **meta)
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return ex


def exercise_or_404(db: Session, exercise_id: UUID) -> SkillExercise:
    ex = db.get(SkillExercise, exercise_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="Exercise not found.")
    return ex


def update_exercise(db: Session, exercise_id: UUID, data: dict) -> SkillExercise:
    ex = exercise_or_404(db, exercise_id)
    meta = _clean_meta({**admin_exercise(ex), **{k: v for k, v in data.items() if v is not None}})
    if meta["is_published"]:
        _check_publishable(ex)
    for k, v in meta.items():
        setattr(ex, k, v)
    db.commit()
    db.refresh(ex)
    return ex


def delete_exercise(db: Session, exercise_id: UUID) -> None:
    db.delete(exercise_or_404(db, exercise_id))
    db.commit()


def replace_exercise_questions(db: Session, exercise_id: UUID, items: list[dict]) -> SkillExercise:
    ex = exercise_or_404(db, exercise_id)
    clean = skill_admin.validate_questions(items)
    if ex.is_published and not clean:
        raise HTTPException(status_code=422, detail="NO_QUESTIONS")
    skill_admin._sync_questions(
        db,
        list(ex.questions),
        clean,
        lambda: SkillExerciseQuestion(exercise_id=ex.id, question=""),
        lambda q: SkillExerciseOption(question_id=q.id, option_text=""),
    )
    db.refresh(ex)
    return ex


def duplicate_exercise(db: Session, exercise_id: UUID) -> SkillExercise:
    src = exercise_or_404(db, exercise_id)
    copy = SkillExercise(lesson_id=src.lesson_id, skill=src.skill, title=skill_admin._copy_title(src.title), instruction=src.instruction,
                         order_index=src.order_index + 1, is_published=False, source=src.source)
    db.add(copy)
    db.flush()
    for q in sorted_questions(src):
        nq = SkillExerciseQuestion(exercise_id=copy.id, question=q.question, question_type=q.question_type, points=q.points,
                                   explanation=q.explanation, order_index=q.order_index, config=q.config)
        db.add(nq)
        db.flush()
        for o in q.options:
            db.add(SkillExerciseOption(question_id=nq.id, option_text=o.option_text, is_correct=o.is_correct, order_index=o.order_index))
    db.commit()
    db.refresh(copy)
    return copy


# ---------- Grammatik rules ----------


def admin_grammar(g: Grammar) -> dict:
    return {"id": g.id, "lesson_id": g.lesson_id, "title": g.title, "content": g.content, "video_url": g.video_url,
            "order_index": g.order_index, "is_published": bool(g.is_published), "content_id": g.content_id}


def _grammar_fields(data: dict) -> dict:
    title = str(data.get("title") or "").strip()
    content = str(data.get("content") or "").strip()
    if not title or len(title) > 255:
        raise HTTPException(status_code=422, detail="Title is required (max 255 characters).")
    if not content:
        raise HTTPException(status_code=422, detail="Content is required.")
    return {"title": title, "content": sanitize_html(content) if "<" in content else content,
            "order_index": int(data.get("order_index") or 1), "is_published": bool(data.get("is_published"))}


def save_grammar(db: Session, lesson_id: UUID | None, data: dict, grammar_id: UUID | None = None) -> Grammar:
    fields = _grammar_fields(data)
    if grammar_id is None:
        g = Grammar(lesson_id=lesson_id, **fields)
        db.add(g)
    else:
        g = db.get(Grammar, grammar_id)
        if g is None:
            raise HTTPException(status_code=404, detail="Grammar not found.")
        for k, v in fields.items():
            setattr(g, k, v)
    db.commit()
    db.refresh(g)
    return g


# ---------- Wortschatz words ----------


def admin_word(v: Vocabulary) -> dict:
    return {"id": v.id, "lesson_id": v.lesson_id, "german_word": v.german_word, "article": v.article, "plural": v.plural,
            "translation": v.translation, "example_sentence": v.example_sentence, "example_translation": v.example_translation,
            "order_index": v.order_index, "is_published": bool(v.is_published), "content_id": v.content_id}


ARTICLES = {"der", "die", "das", None}


def _word_fields(data: dict) -> dict:
    word = str(data.get("german_word") or "").strip()
    translation = str(data.get("translation") or "").strip()
    if not word or len(word) > 255 or not translation or len(translation) > 255:
        raise HTTPException(status_code=422, detail="German word and translation are required (max 255).")
    article = (str(data.get("article") or "").strip().lower() or None)
    if article not in ARTICLES:
        raise HTTPException(status_code=422, detail="Article must be der, die or das.")

    def opt(key, limit):
        value = str(data.get(key) or "").strip()
        return value[:limit] or None

    return {"german_word": word, "translation": translation, "article": article, "plural": opt("plural", 255),
            "example_sentence": opt("example_sentence", 1000), "example_translation": opt("example_translation", 1000),
            "order_index": int(data.get("order_index") or 1), "is_published": bool(data.get("is_published", True))}


def save_word(db: Session, lesson_id: UUID | None, data: dict, word_id: UUID | None = None) -> Vocabulary:
    fields = _word_fields(data)
    if word_id is None:
        if not data.get("order_index"):
            fields["order_index"] = int(db.scalar(select(func.max(Vocabulary.order_index)).where(Vocabulary.lesson_id == lesson_id)) or 0) + 1
        v = Vocabulary(lesson_id=lesson_id, **fields)
        db.add(v)
    else:
        v = db.get(Vocabulary, word_id)
        if v is None:
            raise HTTPException(status_code=404, detail="Word not found.")
        for k, val in fields.items():
            setattr(v, k, val)
    db.commit()
    db.refresh(v)
    return v
