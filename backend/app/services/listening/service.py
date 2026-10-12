from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.listening import ListeningRepository
from app.schemas.listening import (
    ListeningCreate,
    ListeningUpdate,
)


class ListeningService:

    def __init__(self, db: Session):
        self.repository = ListeningRepository(db)

    def get_all(self):
        return self.repository.get_all()

    def get(self, listening_id: str):
        return self.repository.get(listening_id)

    def get_by_lesson(self, lesson_id, published_only: bool = False):
        return self.repository.get_by_lesson(lesson_id, published_only=published_only)

    def create(self, data: ListeningCreate):
        # a Hören task is published only once real audio exists — a new task
        # has none yet unless a legacy external URL is given
        if data.is_published and not data.audio_url:
            raise HTTPException(status_code=409, detail="AUDIO_REQUIRED_TO_PUBLISH")
        return self.repository.create(data)

    def update(
        self,
        listening_id: str,
        data: ListeningUpdate,
    ):
        listening = self.repository.get(listening_id)

        if not listening:
            return None

        publishing = data.is_published is True and not listening.is_published
        audio_after = data.audio_url if "audio_url" in data.model_fields_set else listening.audio_url
        if publishing and not (listening.audio_storage_path or audio_after):
            raise HTTPException(status_code=409, detail="AUDIO_REQUIRED_TO_PUBLISH")
        # imported Hören questions may wait for their answer key until an admin
        # has listened to the uploaded audio — never publish them without it
        if publishing:
            from app.services.lesson_skills.exercises import has_key

            if any(not has_key(q) for q in listening.questions):
                raise HTTPException(status_code=409, detail="ANSWER_KEY_REQUIRED_TO_PUBLISH")

        return self.repository.update(
            listening,
            data,
        )

    def delete(self, listening_id: str):
        listening = self.repository.get(listening_id)

        if not listening:
            return False

        self.repository.delete(listening)

        return True