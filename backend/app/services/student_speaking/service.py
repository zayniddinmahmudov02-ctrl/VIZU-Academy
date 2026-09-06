from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security.roles import UserRole
from app.core.storage.protected_local import ProtectedLegacySpeakingStorage
from app.models.speaking import Speaking
from app.models.student_speaking import STATUS_SUBMITTED, StudentSpeaking
from app.models.task_audio import ALL_AUDIO_FORMATS, CONTENT_TYPE_BY_FORMAT
from app.models.user import User
from app.repositories.student_speaking import StudentSpeakingRepository
from app.repositories.teacher_assignment import TeacherAssignmentRepository
from app.schemas.student_speaking import (
    StudentSpeakingCreate,
    StudentSpeakingUpdate,
    TeacherSpeakingItem,
)
from app.services.assessment_engine.audio_service import resolve_audio_format

MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024  # 25MB — generous for a single spoken answer

storage = ProtectedLegacySpeakingStorage()


def _display_name(user: User) -> str:
    parts = [p for p in (user.first_name, user.last_name) if p]
    return " ".join(parts) if parts else user.username


class StudentSpeakingService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = StudentSpeakingRepository(db)
        self.assignments = TeacherAssignmentRepository(db)

    # ==========================
    # Legacy generic CRUD (unchanged — see app/api/student_speaking/router.py)
    # ==========================

    def get_all(self):
        return self.repository.get_all()

    def get(self, item_id: str):
        return self.repository.get(item_id)

    def create(self, data: StudentSpeakingCreate):
        return self.repository.create(data)

    def update(
        self,
        item_id: str,
        data: StudentSpeakingUpdate,
    ):
        item = self.repository.get(item_id)

        if not item:
            return None

        return self.repository.update(item, data)

    def delete(self, item_id: str):
        item = self.repository.get(item_id)

        if not item:
            return False

        self.repository.delete(item)

        return True

    # ==========================
    # Real student submission workflow
    # ==========================

    async def upload_recording(
        self, user_id: UUID, speaking_id: UUID, file: UploadFile, duration_seconds: int | None
    ) -> StudentSpeaking:
        speaking = self.db.get(Speaking, speaking_id)
        if speaking is None or not speaking.is_published:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaking task not found")

        existing = self.repository.get_by_user_and_speaking(user_id, speaking_id)
        if existing is not None and existing.status == "GRADED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This submission has already been graded and can no longer be re-recorded.",
            )

        audio_format = resolve_audio_format(file.content_type)
        if audio_format not in ALL_AUDIO_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported audio type '{file.content_type}'. Allowed: MP3, WAV, M4A, WebM, OGG.",
            )

        contents = await file.read()
        if len(contents) > MAX_AUDIO_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Audio exceeds the maximum upload size of {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)}MB.",
            )
        await file.seek(0)

        # A cap on speak_seconds isn't modeled on the legacy Speaking task
        # (that's Speaking.speaking_time, enforced client-side by the
        # recorder — see spec section 17, "agar taskda max duration mavjud
        # bo'lmasa mavjud project conventionni tekshir": there is no
        # server-side duration cap anywhere else in this codebase either,
        # e.g. the Assessment Engine's own speaking upload doesn't enforce
        # one server-side — so none is invented here).

        # Re-record semantics: replace the previous file first, same
        # convention as TaskAudio.upload_audio / Assessment Engine's
        # SpeakingSubmission upload.
        if existing is not None and existing.storage_path:
            await storage.delete(existing.storage_path)

        # UUID-based filename — the browser's original filename is never
        # trusted as a storage key (path traversal / collision safety).
        unique_name = f"{uuid4().hex}.{audio_format}"
        storage_path = f"{unique_name}"
        file.filename = unique_name
        await storage.upload(file, storage_path)

        if existing is not None:
            existing.storage_path = storage_path
            existing.filename = unique_name
            existing.content_type = CONTENT_TYPE_BY_FORMAT[audio_format]
            existing.duration_seconds = duration_seconds
            existing.file_size_bytes = len(contents)
            existing.status = STATUS_SUBMITTED
            existing.submitted_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        item = StudentSpeaking(
            user_id=user_id,
            speaking_id=str(speaking_id),
            storage_path=storage_path,
            filename=unique_name,
            content_type=CONTENT_TYPE_BY_FORMAT[audio_format],
            duration_seconds=duration_seconds,
            file_size_bytes=len(contents),
            status=STATUS_SUBMITTED,
            submitted_at=datetime.now(timezone.utc),
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_own(self, user_id: UUID, speaking_id: UUID) -> StudentSpeaking | None:
        return self.repository.get_by_user_and_speaking(user_id, speaking_id)

    def resolve_audio_path(self, item: StudentSpeaking) -> Path:
        return storage.ROOT / item.storage_path

    def authorize_audio_access(self, submission_id: UUID, user: User) -> StudentSpeaking:
        """The single gate for GET /speakings/submissions/{id}/audio —
        owner student, an assigned teacher (scoped through
        TeacherAssignment, never every teacher), or any other admin-panel
        role. 404 in every rejection branch, never 403 — a guessed id for
        another student's recording must not even confirm it exists."""
        item = self.repository.get(str(submission_id))
        if item is None or item.storage_path is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found")

        if item.user_id == user.id:
            return item

        if user.role == UserRole.TEACHER:
            course_ids = [str(c) for c in self.assignments.course_ids_for_teacher(user.id)]
            row = self.repository.get_for_teacher(course_ids, submission_id)
            if row is not None:
                return item
        elif user.role in UserRole.ADMIN_PANEL_ROLES:
            return item

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found")

    # ==========================
    # Teacher grading (IDOR-scoped via TeacherAssignment)
    # ==========================

    def _to_teacher_item(self, row) -> TeacherSpeakingItem:
        submission, speaking, lesson, _module, course, student = row
        return TeacherSpeakingItem(
            id=submission.id,
            student_id=student.id,
            student_name=_display_name(student),
            student_email=student.email,
            course_title=course.title,
            course_level=course.level,
            lesson_title=lesson.title,
            lesson_number=lesson.number,
            speaking_title=speaking.title,
            duration_seconds=submission.duration_seconds,
            status=submission.status,
            submitted_at=submission.submitted_at,
            score=submission.score,
            feedback=submission.feedback,
            reviewed_at=submission.reviewed_at,
        )

    def list_for_teacher(
        self,
        teacher_id: UUID,
        status_filter: str | None = None,
        course_id: str | None = None,
        level: str | None = None,
        lesson_id: str | None = None,
        search: str | None = None,
    ) -> list[TeacherSpeakingItem]:
        course_ids = [str(c) for c in self.assignments.course_ids_for_teacher(teacher_id)]
        rows = self.repository.list_for_teacher(
            course_ids, status=status_filter, course_id=course_id, level=level, lesson_id=lesson_id, search=search
        )
        return [self._to_teacher_item(row) for row in rows]

    def get_for_teacher(self, teacher_id: UUID, submission_id: UUID) -> TeacherSpeakingItem:
        course_ids = [str(c) for c in self.assignments.course_ids_for_teacher(teacher_id)]
        row = self.repository.get_for_teacher(course_ids, submission_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
        return self._to_teacher_item(row)

    def grade(self, teacher_id: UUID, submission_id: UUID, score: int, feedback: str, new_status: str) -> TeacherSpeakingItem:
        self.get_for_teacher(teacher_id, submission_id)

        item = self.repository.get(str(submission_id))
        item.score = score
        item.feedback = feedback
        item.status = new_status
        item.reviewed_by_id = teacher_id
        item.reviewed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(item)

        return self._to_teacher_item(
            (item, item.speaking, item.speaking.lesson, item.speaking.lesson.module, item.speaking.lesson.module.course, item.user)
        )
