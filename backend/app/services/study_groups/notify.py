"""In-app notifications for group events (the existing notifications table;
no e-mail, no Telegram). Chat messages are de-duplicated: a member gets one
unread "new messages" notification per group, not one per message."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import TYPE_COURSE, TYPE_INFORMATION, Notification
from app.models.study_group import GROUP_ACTIVE, MEMBER_ACTIVE, MEMBER_STUDENT, StudyGroup, StudyGroupCourse, StudyGroupMember
from app.services.notification.service import create_notification


def student_link(group_id, tab: str | None = None) -> str:
    return f"/groups/{group_id}" + (f"?tab={tab}" if tab else "")


def teacher_link(group_id, tab: str | None = None) -> str:
    return f"/teacher/groups/{group_id}" + (f"?tab={tab}" if tab else "")


def _student_ids(db: Session, group_id, exclude=None) -> list:
    rows = db.scalars(select(StudyGroupMember.user_id).where(StudyGroupMember.group_id == group_id, StudyGroupMember.status == MEMBER_ACTIVE,
                                                             StudyGroupMember.role == MEMBER_STUDENT))
    return [uid for uid in rows if uid != exclude]


def to_students(db: Session, group: StudyGroup, title: str, message: str, tab: str, exclude=None) -> None:
    for uid in _student_ids(db, group.id, exclude):
        create_notification(db, str(uid), title=title[:255], message=message, type=TYPE_COURSE, link_path=student_link(group.id, tab))


def to_teacher(db: Session, group: StudyGroup, title: str, message: str, tab: str | None = None) -> None:
    create_notification(db, str(group.teacher_id), title=title[:255], message=message, type=TYPE_INFORMATION,
                        link_path=teacher_link(group.id, tab))


def new_message(db: Session, group: StudyGroup, sender_id) -> None:
    recipients = [(uid, student_link(group.id, "chat")) for uid in _student_ids(db, group.id, exclude=sender_id)]
    if group.teacher_id != sender_id:
        recipients.append((group.teacher_id, teacher_link(group.id, "chat")))
    for uid, link in recipients:
        pending = db.scalar(select(Notification.id).where(Notification.user_id == uid, Notification.link_path == link,
                                                          Notification.is_read.is_(False)).limit(1))
        if pending is None:
            create_notification(db, str(uid), title=f"{group.name}: yangi xabar / neue Nachricht",
                                message="Guruh chatida yangi xabar bor.", type=TYPE_INFORMATION, link_path=link)


def submission_to_group_teachers(db: Session, student_id, course_id, what: str) -> None:
    """A student submitted work in a course: tell the teacher of every active
    group the student is in that works with this course."""
    groups = db.scalars(
        select(StudyGroup)
        .join(StudyGroupMember, StudyGroupMember.group_id == StudyGroup.id)
        .join(StudyGroupCourse, StudyGroupCourse.group_id == StudyGroup.id)
        .where(StudyGroupMember.user_id == student_id, StudyGroupMember.status == MEMBER_ACTIVE,
               StudyGroupMember.role == MEMBER_STUDENT, StudyGroupCourse.course_id == course_id, StudyGroup.status == GROUP_ACTIVE)
    ).unique()
    for group in groups:
        create_notification(db, str(group.teacher_id), title=f"{group.name}: {what}", message="Topshiriq tekshiruvni kutmoqda.",
                            type=TYPE_INFORMATION, link_path=f"/teacher/groups/{group.id}/students/{student_id}")
