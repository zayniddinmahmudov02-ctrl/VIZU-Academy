from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_super_admin
from app.db.session import get_db
from app.schemas.mock_exam import (
    ListeningContentCreate,
    ListeningContentResponse,
    ListeningContentUpdate,
    MockQuestionResponse,
    ReadingContentResponse,
    SpeakingTaskCreate,
    SpeakingTaskResponse,
    SpeakingTaskUpdate,
    WritingTaskCreate,
    WritingTaskResponse,
    WritingTaskUpdate,
)
from app.services.mock_exam import content_service

router = APIRouter(
    prefix="/mock-exam",
    tags=["Mock Exam — Content & Questions"],
    dependencies=[Depends(require_super_admin)],
)


# ============================================================
# Reading Content (Lesen)
# ============================================================


@router.get("/teile/{teil_id}/reading-content", response_model=ReadingContentResponse | None)
def get_reading_content(teil_id: UUID, db: Session = Depends(get_db)):
    return content_service.get_reading_content_by_teil(db, teil_id)


# ============================================================
# Listening Content (Hören)
# ============================================================


@router.get("/teile/{teil_id}/listening-content", response_model=ListeningContentResponse | None)
def get_listening_content(teil_id: UUID, db: Session = Depends(get_db)):
    return content_service.get_listening_content_by_teil(db, teil_id)


# Hören audio upload stays in the admin panel (the audio file, image and
# transcript of a Teil) — only the exam *questions* are no longer authored
# here.
@router.post("/listening-content", response_model=ListeningContentResponse, status_code=status.HTTP_201_CREATED)
def create_listening_content(data: ListeningContentCreate, db: Session = Depends(get_db)):
    return content_service.create_listening_content(db, data)


@router.put("/listening-content/{content_id}", response_model=ListeningContentResponse)
def update_listening_content(content_id: UUID, data: ListeningContentUpdate, db: Session = Depends(get_db)):
    content = content_service.update_listening_content(db, content_id, data)
    if content is None:
        raise HTTPException(status_code=404, detail="Listening content not found.")
    return content


@router.delete("/listening-content/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listening_content(content_id: UUID, db: Session = Depends(get_db)):
    if not content_service.delete_listening_content(db, content_id):
        raise HTTPException(status_code=404, detail="Listening content not found.")


# ============================================================
# Writing Task (Schreiben)
# ============================================================


@router.get("/teile/{teil_id}/writing-task", response_model=WritingTaskResponse | None)
def get_writing_task(teil_id: UUID, db: Session = Depends(get_db)):
    return content_service.get_writing_task_by_teil(db, teil_id)


@router.post("/writing-tasks", response_model=WritingTaskResponse, status_code=status.HTTP_201_CREATED)
def create_writing_task(data: WritingTaskCreate, db: Session = Depends(get_db)):
    return content_service.create_writing_task(db, data)


@router.put("/writing-tasks/{task_id}", response_model=WritingTaskResponse)
def update_writing_task(task_id: UUID, data: WritingTaskUpdate, db: Session = Depends(get_db)):
    task = content_service.update_writing_task(db, task_id, data)
    if task is None:
        raise HTTPException(status_code=404, detail="Writing task not found.")
    return task


@router.delete("/writing-tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_writing_task(task_id: UUID, db: Session = Depends(get_db)):
    if not content_service.delete_writing_task(db, task_id):
        raise HTTPException(status_code=404, detail="Writing task not found.")


# ============================================================
# Speaking Task (Sprechen)
# ============================================================


@router.get("/teile/{teil_id}/speaking-task", response_model=SpeakingTaskResponse | None)
def get_speaking_task(teil_id: UUID, db: Session = Depends(get_db)):
    return content_service.get_speaking_task_by_teil(db, teil_id)


@router.post("/speaking-tasks", response_model=SpeakingTaskResponse, status_code=status.HTTP_201_CREATED)
def create_speaking_task(data: SpeakingTaskCreate, db: Session = Depends(get_db)):
    return content_service.create_speaking_task(db, data)


@router.put("/speaking-tasks/{task_id}", response_model=SpeakingTaskResponse)
def update_speaking_task(task_id: UUID, data: SpeakingTaskUpdate, db: Session = Depends(get_db)):
    task = content_service.update_speaking_task(db, task_id, data)
    if task is None:
        raise HTTPException(status_code=404, detail="Speaking task not found.")
    return task


@router.delete("/speaking-tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_speaking_task(task_id: UUID, db: Session = Depends(get_db)):
    if not content_service.delete_speaking_task(db, task_id):
        raise HTTPException(status_code=404, detail="Speaking task not found.")


# ============================================================
# Questions (Question Bank) — read-only: manual question/option authoring
# was removed from the admin panel (Lesen/Hören exam content is now
# produced externally and inserted directly into the DB); the auto-graded
# attempt flow (mock_exam/attempt_router.py) still needs these reads.
# ============================================================


@router.get("/questions", response_model=list[MockQuestionResponse])
def list_questions(
    reading_content_id: UUID | None = None,
    listening_content_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    return content_service.get_questions(db, reading_content_id, listening_content_id)
