from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def write_audit(
    db: Session,
    actor_id: str | None,
    action: str,
    target_user_id: str | None = None,
    details: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor_id,
        target_user_id=target_user_id,
        action=action,
        details=details,
        ip_address=ip_address,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry
