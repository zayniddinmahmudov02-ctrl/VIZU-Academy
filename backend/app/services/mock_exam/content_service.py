from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.listening_content import ListeningContent
from app.models.mock_question import MockQuestion
from app.models.mock_question_option import MockQuestionOption
from app.models.reading_content import ReadingContent
from app.models.speaking_task import SpeakingTask
from app.models.writing_task import WritingTask
from app.schemas.mock_exam import (
    ListeningContentCreate,
    ListeningContentUpdate,
    MockQuestionCreate,
    MockQuestionOptionCreate,
    MockQuestionOptionUpdate,
    MockQuestionUpdate,
    ReadingContentCreate,
    ReadingContentUpdate,
    SpeakingTaskCreate,
    SpeakingTaskUpdate,
    WritingTaskCreate,
    WritingTaskUpdate,
)


def _create_one_to_one(db: Session, model, data):
    """ReadingContent/ListeningContent/WritingTask/SpeakingTask are all 1:1
    with a Teil — reject a second one instead of silently creating a
    duplicate that would violate the DB's unique constraint less clearly."""
    existing = db.scalar(select(model).where(model.teil_id == data.teil_id))
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"This Teil already has {model.__name__} content.",
        )
    obj = model(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def _update(db: Session, model, obj_id: UUID, data):
    obj = db.get(model, obj_id)
    if obj is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def _delete(db: Session, model, obj_id: UUID) -> bool:
    obj = db.get(model, obj_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True


# ============================================================
# Reading Content
# ============================================================


def get_reading_content_by_teil(db: Session, teil_id: UUID):
    return db.scalar(select(ReadingContent).where(ReadingContent.teil_id == teil_id))


def create_reading_content(db: Session, data: ReadingContentCreate):
    return _create_one_to_one(db, ReadingContent, data)


def update_reading_content(db: Session, content_id: UUID, data: ReadingContentUpdate):
    return _update(db, ReadingContent, content_id, data)


def delete_reading_content(db: Session, content_id: UUID) -> bool:
    return _delete(db, ReadingContent, content_id)


# ============================================================
# Listening Content
# ============================================================


def get_listening_content_by_teil(db: Session, teil_id: UUID):
    return db.scalar(select(ListeningContent).where(ListeningContent.teil_id == teil_id))


def create_listening_content(db: Session, data: ListeningContentCreate):
    return _create_one_to_one(db, ListeningContent, data)


def update_listening_content(db: Session, content_id: UUID, data: ListeningContentUpdate):
    return _update(db, ListeningContent, content_id, data)


def delete_listening_content(db: Session, content_id: UUID) -> bool:
    return _delete(db, ListeningContent, content_id)


# ============================================================
# Writing Task
# ============================================================


def get_writing_task_by_teil(db: Session, teil_id: UUID):
    return db.scalar(select(WritingTask).where(WritingTask.teil_id == teil_id))


def create_writing_task(db: Session, data: WritingTaskCreate):
    return _create_one_to_one(db, WritingTask, data)


def update_writing_task(db: Session, task_id: UUID, data: WritingTaskUpdate):
    return _update(db, WritingTask, task_id, data)


def delete_writing_task(db: Session, task_id: UUID) -> bool:
    return _delete(db, WritingTask, task_id)


# ============================================================
# Speaking Task
# ============================================================


def get_speaking_task_by_teil(db: Session, teil_id: UUID):
    return db.scalar(select(SpeakingTask).where(SpeakingTask.teil_id == teil_id))


def create_speaking_task(db: Session, data: SpeakingTaskCreate):
    return _create_one_to_one(db, SpeakingTask, data)


def update_speaking_task(db: Session, task_id: UUID, data: SpeakingTaskUpdate):
    return _update(db, SpeakingTask, task_id, data)


def delete_speaking_task(db: Session, task_id: UUID) -> bool:
    return _delete(db, SpeakingTask, task_id)


# ============================================================
# Questions (Question Bank)
# ============================================================


def get_questions(
    db: Session,
    reading_content_id: UUID | None = None,
    listening_content_id: UUID | None = None,
):
    query = select(MockQuestion).order_by(MockQuestion.sort_order)
    if reading_content_id:
        query = query.where(MockQuestion.reading_content_id == reading_content_id)
    if listening_content_id:
        query = query.where(MockQuestion.listening_content_id == listening_content_id)
    return db.scalars(query).all()


def _validate_question_parent(data: MockQuestionCreate) -> None:
    has_reading = data.reading_content_id is not None
    has_listening = data.listening_content_id is not None
    if has_reading == has_listening:
        raise HTTPException(
            status_code=422,
            detail="A question must belong to exactly one of reading_content_id or listening_content_id.",
        )


def create_question(db: Session, data: MockQuestionCreate):
    _validate_question_parent(data)
    question = MockQuestion(**data.model_dump())
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def update_question(db: Session, question_id: UUID, data: MockQuestionUpdate):
    return _update(db, MockQuestion, question_id, data)


def delete_question(db: Session, question_id: UUID) -> bool:
    return _delete(db, MockQuestion, question_id)


def duplicate_question(db: Session, question_id: UUID) -> MockQuestion | None:
    """Question Bank: clone a question (and its options) so the copy can
    be edited/reused independently, e.g. in a different Teil."""
    original = db.get(MockQuestion, question_id)
    if original is None:
        return None

    clone = MockQuestion(
        reading_content_id=original.reading_content_id,
        listening_content_id=original.listening_content_id,
        question_type=original.question_type,
        question_text=original.question_text,
        explanation=original.explanation,
        correct_text_answer=original.correct_text_answer,
        points=original.points,
        sort_order=original.sort_order,
    )
    db.add(clone)
    db.flush()

    for option in original.options:
        db.add(
            MockQuestionOption(
                question_id=clone.id,
                option_text=option.option_text,
                match_value=option.match_value,
                is_correct=option.is_correct,
                sort_order=option.sort_order,
            )
        )

    db.commit()
    db.refresh(clone)
    return clone


def move_question(
    db: Session,
    question_id: UUID,
    reading_content_id: UUID | None,
    listening_content_id: UUID | None,
) -> MockQuestion | None:
    """Question Bank: move a question to a different reading/listening
    content block."""
    if (reading_content_id is None) == (listening_content_id is None):
        raise HTTPException(
            status_code=422,
            detail="Provide exactly one of reading_content_id or listening_content_id.",
        )

    question = db.get(MockQuestion, question_id)
    if question is None:
        return None

    question.reading_content_id = reading_content_id
    question.listening_content_id = listening_content_id
    db.commit()
    db.refresh(question)
    return question


# ============================================================
# Question Options
# ============================================================


def create_option(db: Session, data: MockQuestionOptionCreate):
    option = MockQuestionOption(**data.model_dump())
    db.add(option)
    db.commit()
    db.refresh(option)
    return option


def update_option(db: Session, option_id: UUID, data: MockQuestionOptionUpdate):
    return _update(db, MockQuestionOption, option_id, data)


def delete_option(db: Session, option_id: UUID) -> bool:
    return _delete(db, MockQuestionOption, option_id)
