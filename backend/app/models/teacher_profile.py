"""One row per teacher account (users.role TEACHER): the permissions that are not a role.

`can_access_student_control` opens the read-only Kontroll area (every student's activity) — default False ("Nein"); only a
SUPER_ADMIN changes it (app.services.teacher.team), every change is written to audit_logs. Course scoping stays in
`teacher_assignments`, group scoping in `study_groups.teacher_id`."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TeacherProfile(BaseModel):
    __tablename__ = "teacher_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_teacher_profiles_user_id"),)

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    can_access_student_control: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    control_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    control_changed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
