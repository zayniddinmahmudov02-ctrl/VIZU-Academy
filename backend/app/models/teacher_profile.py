"""One row per teacher account (users.role TEACHER): the permissions that are not a role, and the public "My Teacher" profile.

`can_access_student_control` opens the read-only Kontroll area (every student's activity) — default False ("Nein"); only a
SUPER_ADMIN changes it (app.services.teacher.team), every change is written to audit_logs. Course scoping stays in
`teacher_assignments`, group scoping in `study_groups.teacher_id`.

Public profile (2026-11-24, migration d9e4a1c7b3f5; rules in app.services.teacher_market): the teacher edits photo (9:16 WebP
made by the server), headline, bio, experience, methodology, exam preparation, languages and levels. Only a SUPER_ADMIN sets
`catalog_hidden` (not listed in My Teacher), `profile_disabled` (profile and courses closed) and `verified` (Verified Teacher).
`rating_avg` / `rating_count` are computed by the server from visible reviews (teacher_reviews) and never written by a request.

Admin who also teaches (2026-11-25, migration e2a7c4f9b1d3): `teaches` = True makes a SUPER_ADMIN account a teacher as well (Team list,
My Teacher catalog, own courses / special lessons) without changing its role; set only through Admin → Team or
app.scripts.team_staff_teacher (audited)."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TeacherProfile(BaseModel):
    __tablename__ = "teacher_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_teacher_profiles_user_id"),
        CheckConstraint("rating_count >= 0", name="ck_teacher_profiles_rating_count"),
        CheckConstraint("experience_years IS NULL OR experience_years BETWEEN 0 AND 70", name="ck_teacher_profiles_experience"),
    )

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    can_access_student_control: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    control_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    control_changed_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # ---- public profile (teacher edits) ----
    photo_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    headline: Mapped[str | None] = mapped_column(String(160), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    teaching_since: Mapped[int | None] = mapped_column(Integer, nullable=True)
    specialization: Mapped[str | None] = mapped_column(String(300), nullable=True)
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    exam_prep: Mapped[list | None] = mapped_column(JSONB(none_as_null=True), nullable=True)
    languages: Mapped[list | None] = mapped_column(JSONB(none_as_null=True), nullable=True)
    levels: Mapped[list | None] = mapped_column(JSONB(none_as_null=True), nullable=True)
    profile_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ---- set by a SUPER_ADMIN only ----
    catalog_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    profile_disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # a SUPER_ADMIN account that also teaches (Team + My Teacher) keeps its role; TEACHER accounts always teach (flag ignored)
    teaches: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    # ---- computed by the server from visible reviews ----
    rating_avg: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=0, server_default="0")
    rating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
