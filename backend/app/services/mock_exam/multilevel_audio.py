"""Multilevel Audio: the Hören audio of the Multilevel Modelltests, managed per Teil ("Aufgabe") by admins.

Slots = the Hören Teile of every Modelltest of the Multilevel level (a Teil's `listening_content`), so an upload plays in
exactly that exam task — a slot of another level/provider cannot be addressed (404). The file itself is an `audio_files`
row (central audio service: upload / trim / keep original); `listening_content.audio_file_id` links it and `audio_url`
carries the marker `mlaudio:<id>` so the existing publish check ("Hören Teil has audio") keeps working untouched.
Replace = attach another file; delete = unlink (the task then has no audio; a PUBLISHED test goes back to DRAFT, since it
can no longer be taken). Questions, answers and scoring are never touched. Students get a short-lived signed stream URL."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.config import settings
from app.core.security.jwt import create_access_token, decode_access_token
from app.models.audio_file import AudioFile
from app.models.certification_provider import CertificationProvider
from app.models.kompetenz import Kompetenz
from app.models.listening_content import ListeningContent
from app.models.mock_exam_level import MockExamLevel
from app.models.model_test import STATUS_DRAFT, STATUS_PUBLISHED, ModelTest
from app.models.teil import Teil
from app.models.user import User
from app.services.audio_files import service as audio_service
from app.services.mock_exam import multilevel_service as ml

PURPOSE = "multilevel_audio"
MARKER = "mlaudio:"


def _err(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def _slots_query():
    return (select(ListeningContent, Teil, Kompetenz, ModelTest)
            .join(Teil, ListeningContent.teil_id == Teil.id).join(Kompetenz, Teil.kompetenz_id == Kompetenz.id)
            .join(ModelTest, Kompetenz.model_test_id == ModelTest.id).join(MockExamLevel, ModelTest.level_id == MockExamLevel.id)
            .join(CertificationProvider, MockExamLevel.provider_id == CertificationProvider.id)
            .where(Kompetenz.type == "HOEREN", MockExamLevel.title == ml.LEVEL_TITLE, CertificationProvider.code == ml.PROVIDER_CODE))


def _slot(db: Session, lc: ListeningContent, teil: Teil, test: ModelTest) -> dict:
    audio = lc.audio_file
    if audio is not None and audio.deleted_at is not None:
        audio = None
    legacy = bool((lc.audio_url or "").strip()) and not lc.audio_file_id
    if audio is not None:
        file_ok = audio_service.path_of(audio) is not None
        status = "ok" if file_ok else "file_missing"
    else:
        status = "external" if legacy else "missing"
    original = db.get(AudioFile, audio.source_id) if audio is not None and audio.source_id else None
    return {"content_id": lc.id, "teil_id": teil.id, "aufgabe_number": teil.sort_order, "title": teil.title, "status": status,
            "audio": audio_service.serialize(audio), "original": audio_service.serialize(original),
            "duration_ms": audio.duration_ms if audio is not None else None, "model_test_id": test.id}


def overview(db: Session) -> dict:
    """Every Modelltest of the Multilevel level with its Hören slots (also tests without Hören tasks yet)."""
    tests = db.scalars(select(ModelTest).join(MockExamLevel, ModelTest.level_id == MockExamLevel.id)
                       .join(CertificationProvider, MockExamLevel.provider_id == CertificationProvider.id)
                       .where(MockExamLevel.title == ml.LEVEL_TITLE, CertificationProvider.code == ml.PROVIDER_CODE)
                       .order_by(ModelTest.sort_order)).all()
    by_test: dict = {t.id: [] for t in tests}
    for lc, teil, komp, test in db.execute(_slots_query().order_by(ModelTest.sort_order, Teil.sort_order)).all():
        by_test[test.id].append(_slot(db, lc, teil, test))
    out = [{"model_test_id": t.id, "title": t.title, "status": t.status, "sort_order": t.sort_order, "slots": by_test[t.id]} for t in tests]
    slots = [s for t in out for s in t["slots"]]
    return {"level": ml.LEVEL_TITLE, "tests": out, "total": len(slots), "with_audio": sum(s["status"] in ("ok", "external") for s in slots)}


def _slot_row(db: Session, content_id: UUID):
    row = db.execute(_slots_query().where(ListeningContent.id == content_id)).first()
    if row is None:
        raise _err(404, "SLOT_NOT_FOUND")
    return row


def slot_status(db: Session, content_id: UUID) -> dict:
    lc, teil, _, test = _slot_row(db, content_id)
    return _slot(db, lc, teil, test)


def _marker(audio: AudioFile) -> str:
    return f"{MARKER}{audio.id}"


async def attach(db: Session, content_id: UUID, audio_id: UUID, user: User) -> dict:
    """Upload / replace: the slot plays this file from now on (a TRIMMED file replaced by it is removed, originals stay)."""
    lc, teil, _, test = _slot_row(db, content_id)
    audio = audio_service.get_active(db, audio_id)
    if audio_service.path_of(audio) is None:
        raise _err(409, "AUDIO_FILE_MISSING")
    old = lc.audio_file
    lc.audio_file_id = audio.id
    lc.audio_url = _marker(audio)
    db.commit()
    write_audit(db, actor_id=user.id, action="multilevel_audio_set", details=f"test={test.id} teil={teil.id} audio={audio.id}")
    if old is not None and old.id != audio.id:
        await audio_service.discard(db, old)
    db.refresh(lc)
    return _slot(db, lc, teil, test)


async def detach(db: Session, content_id: UUID, user: User) -> dict:
    lc, teil, _, test = _slot_row(db, content_id)
    if not lc.audio_file_id and not (lc.audio_url or "").strip():
        raise _err(404, "AUDIO_NOT_FOUND")
    old = lc.audio_file
    lc.audio_file_id = None
    lc.audio_url = ""
    reopened = test.status == STATUS_PUBLISHED
    if reopened:  # no longer takeable: the publish rule needs audio for every Hören Teil
        test.status = STATUS_DRAFT
    db.commit()
    write_audit(db, actor_id=user.id, action="multilevel_audio_removed", details=f"test={test.id} teil={teil.id} unpublished={reopened}")
    if old is not None:
        await audio_service.discard(db, old)
    db.refresh(lc)
    return {**_slot(db, lc, teil, test), "test_unpublished": reopened}


async def trim_slot(db: Session, content_id: UUID, start_ms: int, end_ms: int, user: User) -> dict:
    """Re-trim the slot's audio from its ORIGINAL (the previous cut is replaced, the original stays)."""
    lc, _, _, _ = _slot_row(db, content_id)
    audio = lc.audio_file
    if audio is None or audio.deleted_at is not None:
        raise _err(404, "AUDIO_NOT_FOUND")
    trimmed = await audio_service.trim(db, audio.id, start_ms, end_ms, user)
    return await attach(db, content_id, trimmed.id, user)


def file_path(db: Session, content_id: UUID):
    lc, _, _, _ = _slot_row(db, content_id)
    return audio_service.path_of(lc.audio_file), lc.audio_file.content_type if lc.audio_file else None


# ---------------- students: signed stream URL ----------------


def signed_url(lc: ListeningContent, user_id: UUID | None) -> str | None:
    if user_id is None:
        return None
    token = create_access_token({"sub": str(lc.id), "purpose": PURPOSE, "user_id": str(user_id)},
                                expires_minutes=settings.VIDEO_STREAM_TOKEN_EXPIRE_MINUTES)
    return f"/api/v1/multilevel-exam/audio/{lc.id}?token={token}"


def stream_target(db: Session, content_id: UUID, token: str):
    """(path, content type) for a valid token of this slot: the user must still exist; a non-staff user only gets the
    audio of a PUBLISHED test. Anything else is a 401 / 404, never a path."""
    from jose import JWTError

    from app.core.security.roles import UserRole

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise _err(401, "Invalid or expired audio token") from None
    if payload.get("purpose") != PURPOSE or payload.get("sub") != str(content_id) or not isinstance(payload.get("user_id"), str):
        raise _err(403, "Token does not authorize this audio")
    try:
        user = db.get(User, UUID(payload["user_id"]))
    except ValueError:
        user = None
    if user is None or not user.is_active:
        raise _err(401, "Audio token user no longer exists")
    row = db.execute(_slots_query().where(ListeningContent.id == content_id)).first()
    if row is None:
        raise _err(404, "Audio not found")
    lc, _, _, test = row
    if user.role not in UserRole.ADMIN_PANEL_ROLES and test.status != STATUS_PUBLISHED:
        raise _err(404, "Audio not found")
    path = audio_service.path_of(lc.audio_file)
    if path is None:
        raise _err(404, "AUDIO_FILE_MISSING")
    return path, lc.audio_file.content_type
