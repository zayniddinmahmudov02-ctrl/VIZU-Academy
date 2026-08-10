from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.pagination import clamp_page_params, paginated_response
from app.models.certificate import ALL_CERTIFICATE_SOURCES, SOURCE_COURSE, Certificate
from app.models.user import User

from app.repositories.certificate import (
    CertificateRepository,
)

from app.schemas.certificate import (
    CertificateCreate,
    CertificateUpdate,
)


class CertificateService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.repository = CertificateRepository(db)

    # ==========================
    # CRUD
    # ==========================

    def get_all(self):
        return self.repository.get_all()

    def get(
        self,
        item_id: str,
    ):
        return self.repository.get(item_id)

    def create(
        self,
        data: CertificateCreate,
    ):
        source = data.source or SOURCE_COURSE
        if source not in ALL_CERTIFICATE_SOURCES:
            raise HTTPException(status_code=400, detail=f"Unknown certificate source: {source!r}")
        if source == SOURCE_COURSE and not data.course_id:
            raise HTTPException(status_code=400, detail="course_id is required for COURSE-sourced certificates.")
        data = data.model_copy(update={"source": source})

        # Manual/admin issuance: reuse the same certificate_number /
        # verification_code generators as the automatic issue() path so
        # there is a single source of truth for these unique, non-null
        # fields — never invented ad hoc here or on the client.
        if not data.certificate_number:
            data = data.model_copy(
                update={
                    "certificate_number": self.generate_number(),
                },
            )

        if not data.verification_code:
            data = data.model_copy(
                update={
                    "verification_code": self.generate_verification_code(),
                },
            )

        if not data.score:
            data = data.model_copy(
                update={
                    "score": (
                        data.lesen_score
                        + data.hoeren_score
                        + data.schreiben_score
                        + data.sprechen_score
                    ),
                },
            )

        return self.repository.create(data)

    def update(
        self,
        item_id: str,
        data: CertificateUpdate,
    ):
        item = self.repository.get(item_id)

        if not item:
            return None

        return self.repository.update(
            item,
            data,
        )

    def delete(
        self,
        item_id: str,
    ):
        item = self.repository.get(item_id)

        if not item:
            return False

        self.repository.delete(item)

        return True

    # ==========================
    # Certificate Engine
    # ==========================

    def generate_number(
        self,
    ):

        year = datetime.utcnow().year

        serial = uuid4().hex[:8].upper()

        return f"VIZU-{year}-{serial}"

    def generate_verification_code(
        self,
    ):

        return uuid4().hex.upper()

    def issue(
        self,
        *,
        user_id: str,
        course_id: str,
        level: str,
        lesen_score: int,
        hoeren_score: int,
        schreiben_score: int,
        sprechen_score: int,
        provider: str = "VIZU",
    ):

        total_score = (
            lesen_score
            + hoeren_score
            + schreiben_score
            + sprechen_score
        )

        certificate = Certificate(

            user_id=user_id,

            course_id=course_id,

            provider=provider,

            level=level,

            lesen_score=lesen_score,

            hoeren_score=hoeren_score,

            schreiben_score=schreiben_score,

            sprechen_score=sprechen_score,

            score=total_score,

            certificate_number=self.generate_number(),

            verification_code=self.generate_verification_code(),

            issued_at=datetime.utcnow(),

            is_valid=True,
        )

        self.db.add(certificate)

        self.db.commit()

        self.db.refresh(certificate)

        return certificate

    def verify(
        self,
        verification_code: str,
    ):

        return (
            self.db.query(Certificate)
            .filter(
                Certificate.verification_code
                == verification_code,
                Certificate.is_valid.is_(True),
            )
            .first()
        )

    def history(
        self,
        user_id: str,
    ):

        return (
            self.db.query(Certificate)
            .filter(
                Certificate.user_id == user_id,
            )
            .order_by(
                Certificate.issued_at.desc(),
            )
            .all()
        )

    # ==========================
    # User-centric view (admin Certificate page)
    # ==========================
    #
    # Every certificate currently in this table is course-issued — the
    # unified COURSE/VORBEREITUNG/VIZU_MOCK "source" concept the admin CMS
    # spec asks for needs a new `source` column (a migration), which is
    # blocked in this environment (backend/ has no new-file write
    # permission right now — see final report). `_serialize_grouped`
    # hardcodes source="COURSE" below as an honest reflection of what
    # every existing row actually is, not a real per-row field yet.

    def count_by_user(
        self,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """Users who have at least one certificate, ordered by certificate
        count descending. One GROUP BY aggregate query — never loads every
        certificate row just to count them."""

        base = (
            self.db.query(
                Certificate.user_id,
                func.count(Certificate.id).label("cert_count"),
                func.max(Certificate.issued_at).label("last_issued_at"),
            )
            .group_by(Certificate.user_id)
        )

        total = base.count()

        page, page_size = clamp_page_params(page, page_size)

        rows = (
            base.order_by(func.count(Certificate.id).desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        user_ids = [row.user_id for row in rows]
        users = {u.id: u for u in self.db.query(User).filter(User.id.in_(user_ids)).all()}

        items = [
            {
                "user_id": str(row.user_id),
                "email": users[row.user_id].email if row.user_id in users else None,
                "username": users[row.user_id].username if row.user_id in users else None,
                "first_name": users[row.user_id].first_name if row.user_id in users else None,
                "last_name": users[row.user_id].last_name if row.user_id in users else None,
                "profile_image": users[row.user_id].profile_image if row.user_id in users else None,
                "certificate_count": row.cert_count,
                "last_certificate_at": row.last_issued_at,
            }
            for row in rows
        ]

        return paginated_response(items, total, page, page_size)

    def history_with_source(self, user_id: str) -> list[dict]:
        certs = self.history(user_id)

        return [
            {
                "id": str(c.id),
                "certificate_number": c.certificate_number,
                "level": c.level,
                "source": "COURSE",
                "score": c.score,
                "is_valid": c.is_valid,
                "issued_at": c.issued_at,
                "pdf_url": c.pdf_url,
            }
            for c in certs
        ]

    def invalidate(
        self,
        certificate_id: str,
    ):

        certificate = self.get(certificate_id)

        if not certificate:
            return None

        certificate.is_valid = False

        self.db.commit()

        self.db.refresh(certificate)

        return certificate