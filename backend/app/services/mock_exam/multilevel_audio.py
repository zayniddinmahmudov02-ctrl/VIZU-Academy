"""Multilevel Audio: the Hören audio of the Multilevel Modelltests, managed per Teil ("Aufgabe") by admins.

Slots = the Hören Teile of every Modelltest of the Multilevel level (a Teil's `listening_content`), so an upload plays in
exactly that exam task — a slot of another level/provider cannot be addressed (404). The file itself is an `audio_files`
row (central audio service: upload / trim / keep original); `listening_content.audio_file_id` links it and `audio_url`
carries the marker `mlaudio:<id>` so the existing publish check ("Hören Teil has audio") keeps working untouched.
Replace = attach another file; delete = unlink (the task then has no audio; a PUBLISHED test goes back to DRAFT, since it
can no longer be taken). Questions, answers and scoring are never touched. Students get a short-lived signed stream URL.

Shared audio (Modelltest 1 only, `multilevel_service.SHARED_AUDIO_NUMBERS`): the whole Hören section plays ONE audio for all its Teile
(`kompetenzen.audio_file_id`). It is uploaded / replaced / trimmed / deleted as one slot per Modelltest; the Teile keep their own questions
and answers and need no audio of their own (the per-Teil slots of such a test are refused with 409 SHARED_AUDIO_TEST, an older per-Teil audio is
left alone but not played). The audio length and the exam time (Kompetenz.duration_minutes) are independent: nothing here reads or sets the timer.
The student paper carries one signed URL for the section, the exam page plays it in one player that stays put while the student works through the Teile."""

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
SHARED_PURPOSE = "multilevel_audio_shared"
MARKER = "mlaudio:"


def _err(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def _slots_query():
    return (select(ListeningContent, Teil, Kompetenz, ModelTest)
            .join(Teil, ListeningContent.teil_id == Teil.id).join(Kompetenz, Teil.kompetenz_id == Kompetenz.id)
            .join(ModelTest, Kompetenz.model_test_id == ModelTest.id).join(MockExamLevel, ModelTest.level_id == MockExamLevel.id)
            .join(CertificationProvider, MockExamLevel.provider_id == CertificationProvider.id)
            .where(Kompetenz.type == "HOEREN", MockExamLevel.title == ml.LEVEL_TITLE, CertificationProvider.code == ml.PROVIDER_CODE))


def _status_of(audio: AudioFile | None, legacy: bool = False) -> str:
    if audio is not None and audio.deleted_at is None:
        return "ok" if audio_service.path_of(audio) is not None else "file_missing"
    return "external" if legacy else "missing"


def _slot(db: Session, lc: ListeningContent, teil: Teil, test: ModelTest, shared: dict | None = None) -> dict:
    if shared is not None:  # shared-audio test: the Teil plays the section's audio, whatever its own row says
        return {"content_id": lc.id, "teil_id": teil.id, "aufgabe_number": teil.sort_order, "title": teil.title, "status": shared["status"],
                "audio": None, "original": None, "duration_ms": shared["duration_ms"], "model_test_id": test.id, "shared": True}
    audio = lc.audio_file
    if audio is not None and audio.deleted_at is not None:
        audio = None
    legacy = bool((lc.audio_url or "").strip()) and not lc.audio_file_id
    status = _status_of(audio, legacy)
    original = db.get(AudioFile, audio.source_id) if audio is not None and audio.source_id else None
    return {"content_id": lc.id, "teil_id": teil.id, "aufgabe_number": teil.sort_order, "title": teil.title, "status": status,
            "audio": audio_service.serialize(audio), "original": audio_service.serialize(original),
            "duration_ms": audio.duration_ms if audio is not None else None, "model_test_id": test.id, "shared": False}


def overview(db: Session) -> dict:
    """Every Modelltest of the Multilevel level with its Hören slots (also tests without Hören tasks yet)."""
    tests = db.scalars(select(ModelTest).join(MockExamLevel, ModelTest.level_id == MockExamLevel.id)
                       .join(CertificationProvider, MockExamLevel.provider_id == CertificationProvider.id)
                       .where(MockExamLevel.title == ml.LEVEL_TITLE, CertificationProvider.code == ml.PROVIDER_CODE)
                       .order_by(ModelTest.sort_order)).all()
    by_test: dict = {t.id: [] for t in tests}
    shared_of: dict = {}
    for lc, teil, komp, test in db.execute(_slots_query().order_by(ModelTest.sort_order, Teil.sort_order)).all():
        if ml.shared_audio_test(test) and test.id not in shared_of:
            shared_of[test.id] = _shared_status(db, komp, test)
        by_test[test.id].append(_slot(db, lc, teil, test, shared_of.get(test.id)))
    out = [{"model_test_id": t.id, "title": t.title, "status": t.status, "sort_order": t.sort_order, "slots": by_test[t.id], "shared": shared_of.get(t.id)} for t in tests]
    slots = [s for t in out for s in t["slots"]]
    return {"level": ml.LEVEL_TITLE, "tests": out, "total": len(slots), "with_audio": sum(s["status"] in ("ok", "external") for s in slots)}


def _slot_row(db: Session, content_id: UUID):
    row = db.execute(_slots_query().where(ListeningContent.id == content_id)).first()
    if row is None:
        raise _err(404, "SLOT_NOT_FOUND")
    return row


def slot_status(db: Session, content_id: UUID) -> dict:
    lc, teil, komp, test = _slot_row(db, content_id)
    return _slot(db, lc, teil, test, _shared_status(db, komp, test) if ml.shared_audio_test(test) else None)


def _marker(audio: AudioFile) -> str:
    return f"{MARKER}{audio.id}"


async def attach(db: Session, content_id: UUID, audio_id: UUID, user: User) -> dict:
    """Upload / replace: the slot plays this file from now on (a TRIMMED file replaced by it is removed, originals stay)."""
    lc, teil, _, test = _slot_row(db, content_id)
    _refuse_shared(test)
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
    _refuse_shared(test)
    if not lc.audio_file_id and not (lc.audio_url or "").strip():
        raise _err(404, "AUDIO_NOT_FOUND")
    old = lc.audio_file
    lc.audio_file_id = None
    lc.audio_url = ""
    reopened = test.status == STATUS_PUBLISHED and not ml.open_test(test)
    if reopened:  # no longer takeable: the publish rule needs audio for every Hören Teil (not for the open Modelltest 1–6)
        test.status = STATUS_DRAFT
    db.commit()
    write_audit(db, actor_id=user.id, action="multilevel_audio_removed", details=f"test={test.id} teil={teil.id} unpublished={reopened}")
    if old is not None:
        await audio_service.discard(db, old)
    db.refresh(lc)
    return {**_slot(db, lc, teil, test), "test_unpublished": reopened}


async def trim_slot(db: Session, content_id: UUID, start_ms: int, end_ms: int, user: User) -> dict:
    """Re-trim the slot's audio from its ORIGINAL (the previous cut is replaced, the original stays)."""
    lc, _, _, test = _slot_row(db, content_id)
    _refuse_shared(test)
    audio = lc.audio_file
    if audio is None or audio.deleted_at is not None:
        raise _err(404, "AUDIO_NOT_FOUND")
    trimmed = await audio_service.trim(db, audio.id, start_ms, end_ms, user)
    return await attach(db, content_id, trimmed.id, user)


def file_path(db: Session, content_id: UUID):
    lc, _, _, _ = _slot_row(db, content_id)
    return audio_service.path_of(lc.audio_file), lc.audio_file.content_type if lc.audio_file else None


# ---------------- shared audio of one Modelltest (Modelltest 1) ----------------


def _refuse_shared(test: ModelTest) -> None:
    if ml.shared_audio_test(test):
        raise _err(409, "SHARED_AUDIO_TEST: this Modelltest plays one shared audio for all Hören Teile — use the shared audio.")


def _shared_row(db: Session, model_test_id: UUID) -> tuple[Kompetenz, ModelTest]:
    row = db.execute(select(Kompetenz, ModelTest).join(ModelTest, Kompetenz.model_test_id == ModelTest.id)
                     .join(MockExamLevel, ModelTest.level_id == MockExamLevel.id).join(CertificationProvider, MockExamLevel.provider_id == CertificationProvider.id)
                     .where(ModelTest.id == model_test_id, Kompetenz.type == "HOEREN", MockExamLevel.title == ml.LEVEL_TITLE,
                            CertificationProvider.code == ml.PROVIDER_CODE)).first()
    if row is None or not ml.shared_audio_test(row[1]):
        raise _err(404, "SHARED_AUDIO_NOT_AVAILABLE")
    return row[0], row[1]


def _shared_status(db: Session, komp: Kompetenz, test: ModelTest) -> dict:
    audio = komp.audio_file if komp.audio_file is not None and komp.audio_file.deleted_at is None else None
    original = db.get(AudioFile, audio.source_id) if audio is not None and audio.source_id else None
    teile = db.execute(select(Teil, ListeningContent).outerjoin(ListeningContent, ListeningContent.teil_id == Teil.id)
                       .where(Teil.kompetenz_id == komp.id).order_by(Teil.sort_order)).all()
    from sqlalchemy import func

    from app.models.mock_question import MockQuestion

    counts = dict(db.execute(select(MockQuestion.listening_content_id, func.count()).where(MockQuestion.listening_content_id.in_([lc.id for _, lc in teile if lc is not None]))
                             .group_by(MockQuestion.listening_content_id)).all()) if teile else {}
    return {"model_test_id": test.id, "kompetenz_id": komp.id, "title": test.title, "status": _status_of(audio), "audio": audio_service.serialize(audio),
            "original": audio_service.serialize(original), "duration_ms": audio.duration_ms if audio is not None else None,
            # the exam time is its own setting: shown for orientation, never derived from the audio
            "exam_minutes": komp.duration_minutes,
            "teile": [{"teil_id": t.id, "aufgabe_number": t.sort_order, "title": t.title, "questions": counts.get(lc.id, 0) if lc is not None else 0} for t, lc in teile]}


def shared_status(db: Session, model_test_id: UUID) -> dict:
    komp, test = _shared_row(db, model_test_id)
    return _shared_status(db, komp, test)


async def attach_shared(db: Session, model_test_id: UUID, audio_id: UUID, user: User) -> dict:
    """Upload / replace: all Hören Teile of this Modelltest play this (already uploaded, possibly trimmed) file from now on."""
    komp, test = _shared_row(db, model_test_id)
    audio = audio_service.get_active(db, audio_id)
    if audio_service.path_of(audio) is None:
        raise _err(409, "AUDIO_FILE_MISSING")
    old = komp.audio_file
    komp.audio_file_id = audio.id
    db.commit()
    write_audit(db, actor_id=user.id, action="multilevel_audio_shared_set", details=f"test={test.id} audio={audio.id}")
    if old is not None and old.id != audio.id:
        await audio_service.discard(db, old)  # a TRIMMED file nobody uses any more; originals stay
    db.refresh(komp)
    return _shared_status(db, komp, test)


async def detach_shared(db: Session, model_test_id: UUID, user: User) -> dict:
    komp, test = _shared_row(db, model_test_id)
    if komp.audio_file_id is None:
        raise _err(404, "AUDIO_NOT_FOUND")
    old = komp.audio_file
    komp.audio_file_id = None
    reopened = test.status == STATUS_PUBLISHED and not ml.open_test(test)
    if reopened:  # a Modelltest without its audio cannot be taken (the open Modelltest 1–6 can: Hören then has no player)
        test.status = STATUS_DRAFT
    db.commit()
    write_audit(db, actor_id=user.id, action="multilevel_audio_shared_removed", details=f"test={test.id} unpublished={reopened}")
    if old is not None:
        await audio_service.discard(db, old)
    db.refresh(komp)
    return {**_shared_status(db, komp, test), "test_unpublished": reopened}


async def trim_shared(db: Session, model_test_id: UUID, start_ms: int, end_ms: int, user: User) -> dict:
    """Re-trim the shared audio from its ORIGINAL (the previous cut is replaced, the original stays)."""
    komp, _ = _shared_row(db, model_test_id)
    audio = komp.audio_file
    if audio is None or audio.deleted_at is not None:
        raise _err(404, "AUDIO_NOT_FOUND")
    trimmed = await audio_service.trim(db, audio.id, start_ms, end_ms, user)
    return await attach_shared(db, model_test_id, trimmed.id, user)


def shared_file_path(db: Session, model_test_id: UUID):
    komp, _ = _shared_row(db, model_test_id)
    return audio_service.path_of(komp.audio_file), komp.audio_file.content_type if komp.audio_file else None


def is_shared(db: Session, komp: Kompetenz) -> bool:
    """True for the Hören section of a Multilevel Modelltest in shared-audio mode."""
    if komp.type != "HOEREN":
        return False
    test = db.get(ModelTest, komp.model_test_id)
    return ml.shared_audio_test(test) and test.level_id in db.scalars(select(MockExamLevel.id).where(MockExamLevel.title == ml.LEVEL_TITLE)).all()


def shared_for_paper(db: Session, komp: Kompetenz, user_id: UUID | None) -> dict | None:
    """What the exam paper hands to the player: one signed URL for the whole section (None when the audio is not there)."""
    audio = komp.audio_file
    if audio is None or audio.deleted_at is not None or audio_service.path_of(audio) is None or user_id is None:
        return None
    token = create_access_token({"sub": str(komp.id), "purpose": SHARED_PURPOSE, "user_id": str(user_id)}, expires_minutes=settings.VIDEO_STREAM_TOKEN_EXPIRE_MINUTES)
    return {"url": f"/api/v1/multilevel-exam/audio-shared/{komp.id}?token={token}", "duration_ms": audio.duration_ms, "kompetenz_id": komp.id}


# ---------------- students: signed stream URL ----------------


def signed_url(lc: ListeningContent, user_id: UUID | None) -> str | None:
    if user_id is None:
        return None
    token = create_access_token({"sub": str(lc.id), "purpose": PURPOSE, "user_id": str(user_id)},
                                expires_minutes=settings.VIDEO_STREAM_TOKEN_EXPIRE_MINUTES)
    return f"/api/v1/multilevel-exam/audio/{lc.id}?token={token}"


def stream_target_shared(db: Session, komp_id: UUID, token: str):
    """(path, content type) for a valid token of this Hören section's shared audio; the same rules as `stream_target`: the user must still exist, a
    non-staff user only gets the audio of a PUBLISHED test, a token of another section or purpose is refused."""
    from jose import JWTError

    from app.core.security.roles import UserRole

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise _err(401, "Invalid or expired audio token") from None
    if payload.get("purpose") != SHARED_PURPOSE or payload.get("sub") != str(komp_id) or not isinstance(payload.get("user_id"), str):
        raise _err(403, "Token does not authorize this audio")
    try:
        user = db.get(User, UUID(payload["user_id"]))
    except ValueError:
        user = None
    if user is None or not user.is_active:
        raise _err(401, "Audio token user no longer exists")
    komp = db.get(Kompetenz, komp_id)
    test = db.get(ModelTest, komp.model_test_id) if komp is not None else None
    if komp is None or test is None or not is_shared(db, komp):
        raise _err(404, "Audio not found")
    if user.role not in UserRole.ADMIN_PANEL_ROLES and test.status != STATUS_PUBLISHED:
        raise _err(404, "Audio not found")
    path = audio_service.path_of(komp.audio_file) if komp.audio_file is not None and komp.audio_file.deleted_at is None else None
    if path is None:
        raise _err(404, "AUDIO_FILE_MISSING")
    return path, komp.audio_file.content_type


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
