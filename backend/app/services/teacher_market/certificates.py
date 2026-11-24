"""Teacher certificates: the teacher uploads (title, issuer, date, level, image or PDF), a SUPER_ADMIN verifies or rejects.

* A new or re-uploaded certificate is PENDING; only VERIFIED ones appear on the public profile with the verified mark.
* The teacher may delete own PENDING / REJECTED certificates; a VERIFIED one stays (the admin can reject it later).
* The file is served only here: a verified certificate to any logged-in user (it is public on the profile), any other only to
  its teacher and to admin-panel staff. Never a public URL; private, no-store."""

from datetime import date
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.security.roles import UserRole
from app.models.teacher_market import CERT_PENDING, CERT_REJECTED, CERT_VERIFIED, TeacherCertificate
from app.models.user import User
from app.services.teacher_market import common as c
from app.services.teacher_market import media

MAX_PER_TEACHER = 30
STAFF = (UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CONTENT_MANAGER, UserRole.SUPPORT, UserRole.PAYMENT_MANAGER)


def _date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        d = date.fromisoformat(value.strip())
    except ValueError:
        raise c.err(422, "ISSUED_ON_INVALID") from None
    if d > c.now().date() or d.year < 1950:
        raise c.err(422, "ISSUED_ON_INVALID")
    return d


async def upload(db: Session, teacher: User, *, title: str, issuer: str, issued_on: str | None, level: str | None, file) -> dict:
    count = db.scalar(select(func.count()).select_from(TeacherCertificate).where(TeacherCertificate.teacher_id == teacher.id)) or 0
    if count >= MAX_PER_TEACHER:
        raise c.err(409, "TOO_MANY_CERTIFICATES")
    title_ = c.one_line(title, "title", 200, min_len=2, required=True)
    issuer_ = c.one_line(issuer, "issuer", 200, min_len=2, required=True)
    when = _date(issued_on)
    level_ = c.one_line(level, "level", 40)
    if file is None or not file.filename:
        raise c.err(422, "FILE_REQUIRED")
    data = await file.read()
    name, kind = media.save_certificate(data, file.filename, file.content_type)
    row = TeacherCertificate(teacher_id=teacher.id, title=title_, issuer=issuer_, issued_on=when, level=level_, file_name=name, file_type=kind,
                             status=CERT_PENDING)
    db.add(row)
    db.flush()
    c.notify_admins(db, "Yangi sertifikat / Neues Zertifikat", f"{c.display_name(teacher)}: {title_} ({issuer_}) — tekshirish kerak.",
                    "/admin/lehrer-marktplatz?tab=zertifikate")
    db.commit()
    return {"id": row.id, "status": row.status}


def delete_own(db: Session, teacher: User, cert_id) -> dict:
    row = db.get(TeacherCertificate, c.parse_uuid(cert_id))
    if row is None or row.teacher_id != teacher.id:
        raise c.err(404, "CERTIFICATE_NOT_FOUND")
    if row.status == CERT_VERIFIED:
        raise c.err(409, "CERTIFICATE_VERIFIED")
    name = row.file_name
    db.delete(row)
    db.commit()
    media.remove_certificate(name)
    return {"deleted": True}


def file_for(db: Session, viewer: User, cert_id) -> tuple[Path, str, str]:
    row = db.get(TeacherCertificate, c.parse_uuid(cert_id))
    if row is None:
        raise c.err(404, "CERTIFICATE_NOT_FOUND")
    allowed = row.status == CERT_VERIFIED or viewer.id == row.teacher_id or viewer.role in STAFF
    if not allowed:
        raise c.err(404, "CERTIFICATE_NOT_FOUND")
    if row.status == CERT_VERIFIED and viewer.id != row.teacher_id and viewer.role not in STAFF:
        teacher = db.get(User, row.teacher_id)
        if not c.listed(teacher, c.profile_of(db, row.teacher_id)):
            raise c.err(404, "CERTIFICATE_NOT_FOUND")
    path = media.certificate_path(row.file_name)
    if not path.is_file():
        raise c.err(404, "CERTIFICATE_FILE_MISSING")
    media_type = "application/pdf" if row.file_type == "pdf" else "image/webp"
    return path, media_type, f"zertifikat{'.pdf' if row.file_type == 'pdf' else '.webp'}"


# ---------- admin ----------

def admin_list(db: Session, status: str | None) -> list[dict]:
    q = select(TeacherCertificate, User).join(User, User.id == TeacherCertificate.teacher_id)
    if status in (CERT_PENDING, CERT_VERIFIED, CERT_REJECTED):
        q = q.where(TeacherCertificate.status == status)
    rows = db.execute(q.order_by(TeacherCertificate.status != CERT_PENDING, TeacherCertificate.created_at.desc()).limit(300)).all()
    return [{"id": r.id, "teacher": {"id": u.id, "name": c.display_name(u)}, "title": r.title, "issuer": r.issuer, "issued_on": r.issued_on,
             "level": r.level, "file_type": r.file_type, "file_url": f"/api/v1/my-teacher/certificates/{r.id}/file", "status": r.status,
             "reject_reason": r.reject_reason, "created_at": r.created_at, "reviewed_at": r.reviewed_at} for r, u in rows]


def admin_review(db: Session, admin: User, cert_id, decision: str, reason: str | None, ip: str | None) -> dict:
    row = db.scalar(select(TeacherCertificate).where(TeacherCertificate.id == c.parse_uuid(cert_id)).with_for_update())
    if row is None:
        raise c.err(404, "CERTIFICATE_NOT_FOUND")
    if decision == "verify":
        row.status, row.reject_reason = CERT_VERIFIED, None
        c.notify(db, row.teacher_id, "Sertifikat tasdiqlandi / Zertifikat bestätigt", f"«{row.title}» profilingizda tasdiqlangan holda ko'rinadi.",
                 "/teacher/profil")
    elif decision == "reject":
        text = c.one_line(reason, "reason", 500, min_len=3, required=True)
        row.status, row.reject_reason = CERT_REJECTED, text
        c.notify(db, row.teacher_id, "Sertifikat rad etildi / Zertifikat abgelehnt", f"«{row.title}»: {text}", "/teacher/profil")
    else:
        raise c.err(422, "DECISION_INVALID")
    row.reviewed_by, row.reviewed_at = admin.id, c.now()
    db.commit()
    write_audit(db, actor_id=admin.id, action=f"teacher_certificate_{decision}", target_user_id=row.teacher_id,
                details=f"certificate={row.id} {row.title}" + (f", reason={row.reject_reason}" if row.reject_reason else ""), ip_address=ip)
    return {"id": row.id, "status": row.status}
