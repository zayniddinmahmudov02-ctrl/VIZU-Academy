"""Multilevel groups (owner 2026-11-28): a group linked to the Vorbereitung level "Multilevel B1–C1" (study_groups.mock_exam_level_id, set by a
SUPER_ADMIN only — it opens the paid Modelltests for the active members, see vizu_pay.access.multilevel_group_levels) shows its members'
Modelltest results. READ ONLY: a teacher never changes a score (Schreiben / Sprechen are graded and overridden by the Super Admin in
Admin → Multilevel). Source = mock_test_attempts + mock_attempt_sections (every attempt is kept), scored by mock_exam.multilevel_exam_service.

* overview (group managers): one row per active student member — Modelltests taken (with a finished attempt), attempts, last attempt, the
  four section scores + total + result of the latest finished attempt, the best total and the estimated level ("taxminiy": the average of the
  sections in the section bands, multilevel_exam_service.estimated_level).
* student_detail (managers): every Modelltest of the level with all attempts of that student (sections: score, raw points, level, feedback).
* mine (an active student member): the same list for the student's own attempts.
Only attempts on Modelltests of the group's level count. An attempt still IN_PROGRESS is listed without any score (the student sees results
only after all four sections are closed; teachers see the same)."""

from collections import defaultdict
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mock_attempt_section import SECTION_OPEN, MockAttemptSection
from app.models.mock_exam_level import MockExamLevel
from app.models.mock_speaking_submission import MockSpeakingSubmission
from app.models.mock_test_attempt import STATUS_IN_PROGRESS, MockTestAttempt
from app.models.mock_writing_submission import MockWritingSubmission
from app.models.model_test import STATUS_ARCHIVED, STATUS_PUBLISHED, ModelTest
from app.models.speaking_task import SpeakingTask
from app.models.study_group import MEMBER_ACTIVE, MEMBER_STUDENT, StudyGroup, StudyGroupMember
from app.models.teil import Teil
from app.models.user import User
from app.models.writing_task import WritingTask
from app.services.mock_exam import multilevel_exam_service as exam
from app.services.study_groups.access import display_name


def _level(db: Session, group: StudyGroup) -> MockExamLevel:
    level = db.get(MockExamLevel, group.mock_exam_level_id) if group.mock_exam_level_id else None
    if level is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_a_multilevel_group")
    return level


def _tests(db: Session, level_id) -> list[ModelTest]:
    return list(db.scalars(select(ModelTest).where(ModelTest.level_id == level_id).order_by(ModelTest.sort_order, ModelTest.title)))


def _attempts(db: Session, test_ids: list, user_ids: list) -> list[MockTestAttempt]:
    if not test_ids or not user_ids:
        return []
    return list(db.scalars(select(MockTestAttempt).where(MockTestAttempt.model_test_id.in_(test_ids), MockTestAttempt.user_id.in_(user_ids))
                           .order_by(MockTestAttempt.started_at.desc())))


def _sections(db: Session, attempts: list[MockTestAttempt]) -> dict:
    out: dict = defaultdict(dict)
    if attempts:
        for s in db.scalars(select(MockAttemptSection).where(MockAttemptSection.attempt_id.in_([a.id for a in attempts]))):
            out[s.attempt_id][s.section_type] = s
    return out


def _work(db: Session, a: MockTestAttempt) -> dict:
    """The student's own Schreiben texts and Sprechen recordings of one attempt (recordings by id: streamed through access-checked endpoints)."""
    out: dict = {"writings": [], "recordings": []}
    for w, task, teil in db.execute(select(MockWritingSubmission, WritingTask, Teil).join(WritingTask, MockWritingSubmission.writing_task_id == WritingTask.id)
                                    .join(Teil, WritingTask.teil_id == Teil.id).where(MockWritingSubmission.attempt_id == a.id)):
        out["writings"].append({"teil": teil.title, "answer_text": w.answer_text, "word_count": w.word_count})
    for r, teil in db.execute(select(MockSpeakingSubmission, Teil).join(SpeakingTask, MockSpeakingSubmission.speaking_task_id == SpeakingTask.id)
                              .join(Teil, SpeakingTask.teil_id == Teil.id).where(MockSpeakingSubmission.attempt_id == a.id)):
        out["recordings"].append({"submission_id": r.id, "teil": teil.title})
    out["writings"].sort(key=lambda x: x["teil"])
    out["recordings"].sort(key=lambda x: x["teil"])
    return out


def _view(a: MockTestAttempt, test: ModelTest | None, secs: dict, settings: dict, db: Session | None = None) -> dict:
    """`db` given (drill-down): also the AI explanation of Schreiben / Sprechen and the student's texts / recordings."""
    finished = a.status != STATUS_IN_PROGRESS
    sections = {}
    for t in exam.SECTIONS:
        s = secs.get(t)
        if s is None or not finished:
            sections[t] = {"status": s.status if s else "NOT_STARTED"} if not finished else None
            continue
        sections[t] = {"score": s.score, "max": exam.SECTION_MAX, "level": s.level, "status": s.status, "raw_points": s.raw_points,
                       "raw_max": s.raw_max, "no_key": exam._unscorable(s), "feedback": s.feedback,
                       "awaiting_grading": t in exam.GRADED_SECTIONS and s.status != SECTION_OPEN and s.score is None,
                       "score_source": s.score_source, "ai_status": s.ai_status, "ai_raw": s.ai_raw, "ai_raw_max": s.ai_raw_max}
        if db is not None and t in exam.GRADED_SECTIONS:
            sections[t]["evaluation"] = exam.public_evaluation(exam._latest_ai(db, s.id))
    counted = ([sections[t]["score"] if sections[t] else None for t in exam.SECTIONS if not (sections[t] and sections[t]["no_key"])]
               if finished else [])
    view = {"attempt_id": a.id, "model_test_id": a.model_test_id, "title": test.title if test else "", "status": a.status,
            "started_at": a.started_at, "submitted_at": a.submitted_at, "duration_seconds": a.time_spent_seconds if finished else None,
            "total_score": a.total_score if finished else None, "max_score": (a.max_score or exam.TOTAL_MAX) if finished else None,
            "result_level": a.result_level if finished else None,
            "estimated_level": exam.estimated_level(counted, settings) if finished else None, "sections": sections}
    if db is not None and finished:
        view |= _work(db, a)
    return view


def _students(db: Session, group: StudyGroup) -> list[User]:
    return list(db.scalars(select(User).join(StudyGroupMember, StudyGroupMember.user_id == User.id).where(
        StudyGroupMember.group_id == group.id, StudyGroupMember.role == MEMBER_STUDENT, StudyGroupMember.status == MEMBER_ACTIVE)))


def _test_ref(t: ModelTest) -> dict:
    return {"id": t.id, "title": t.title, "number": t.sort_order, "status": t.status, "available": t.status == STATUS_PUBLISHED}


def overview(db: Session, group: StudyGroup) -> dict:
    level = _level(db, group)
    tests = _tests(db, level.id)
    by_id = {t.id: t for t in tests}
    students = sorted(_students(db, group), key=lambda u: display_name(u).lower())
    attempts = _attempts(db, list(by_id), [u.id for u in students])
    secs, settings = _sections(db, attempts), exam.get_settings(db)
    per_user: dict = defaultdict(list)
    for a in attempts:
        per_user[a.user_id].append(a)
    rows = []
    for u in students:
        mine = per_user.get(u.id, [])
        done = [a for a in mine if a.status != STATUS_IN_PROGRESS]
        latest = done[0] if done else None
        totals = [a.total_score for a in done if a.total_score is not None]
        rows.append({"user_id": u.id, "name": display_name(u), "email": u.email, "attempts": len(mine),
                     "tests_taken": len({a.model_test_id for a in done}), "last_attempt_at": mine[0].started_at if mine else None,
                     "in_progress": sum(1 for a in mine if a.status == STATUS_IN_PROGRESS),
                     "latest": _view(latest, by_id.get(latest.model_test_id), secs.get(latest.id, {}), settings) if latest else None,
                     "best_total": max(totals) if totals else None})
    test_rows = [_test_ref(t) | {"attempts": sum(1 for a in attempts if a.model_test_id == t.id)}
                 for t in tests if t.status != STATUS_ARCHIVED or any(a.model_test_id == t.id for a in attempts)]
    return {"level": {"id": level.id, "title": level.title}, "section_max": exam.SECTION_MAX, "total_max": exam.TOTAL_MAX,
            "tests": test_rows, "students": rows}


def _per_test(db: Session, level: MockExamLevel, user_id: UUID) -> list[dict]:
    tests = _tests(db, level.id)
    attempts = _attempts(db, [t.id for t in tests], [user_id])
    secs, settings = _sections(db, attempts), exam.get_settings(db)
    out = []
    for t in tests:
        mine = [_view(a, t, secs.get(a.id, {}), settings, db) for a in attempts if a.model_test_id == t.id]
        if t.status == STATUS_ARCHIVED and not mine:
            continue
        totals = [v["total_score"] for v in mine if v["total_score"] is not None]
        out.append(_test_ref(t) | {"attempts": mine, "best_total": max(totals) if totals else None})
    return out


def student_detail(db: Session, group: StudyGroup, student_id: UUID) -> dict:
    level = _level(db, group)
    user = db.get(User, student_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return {"level": {"id": level.id, "title": level.title}, "student": {"user_id": user.id, "name": display_name(user), "email": user.email},
            "section_max": exam.SECTION_MAX, "total_max": exam.TOTAL_MAX, "tests": _per_test(db, level, user.id)}


def recording(db: Session, viewer: User, group: StudyGroup, submission_id: UUID):
    """A Sprechen recording for the group's teacher: only of a student who is (or was) a student member of this group, on a Modelltest of the
    group's level — anything else is a 404 (the same answer as a missing file)."""
    level = _level(db, group)
    row = db.execute(select(MockTestAttempt.user_id, ModelTest.level_id).join(MockSpeakingSubmission, MockSpeakingSubmission.attempt_id == MockTestAttempt.id)
                     .join(ModelTest, MockTestAttempt.model_test_id == ModelTest.id).where(MockSpeakingSubmission.id == submission_id)).first()
    member = row and db.scalar(select(StudyGroupMember.id).where(StudyGroupMember.group_id == group.id, StudyGroupMember.user_id == row[0],
                                                                 StudyGroupMember.role == MEMBER_STUDENT))
    if not row or row[1] != level.id or not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RECORDING_NOT_FOUND")
    return exam.recording_file(db, viewer, submission_id, staff=True)


def mine(db: Session, group: StudyGroup, user: User) -> dict:
    level = _level(db, group)
    return {"level": {"id": level.id, "title": level.title}, "section_max": exam.SECTION_MAX, "total_max": exam.TOTAL_MAX,
            "tests": _per_test(db, level, user.id)}
