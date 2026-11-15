"""Shared fixture of the Medienwelt integration tests (books / payments / audio): a throwaway database (VIZU_WB_TEST_DB_URL, DATABASE_NAME the
same), a temporary private storage, five users (two students, one for rate limits, a normal ADMIN, a SUPER_ADMIN) and small helpers. Everything
the tests create is removed again."""

import os
import shutil
import subprocess
import tempfile
import unittest
import uuid
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")
FFMPEG = shutil.which(os.environ.get("FFMPEG_BIN", "ffmpeg"))
PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")


def make_png(width: int = 30, height: int = 20, color: str = "white") -> bytes:
    """A real, decodable PNG (the tiny `PNG` above opens but is a damaged image — fine for a cover sniff test, not for a receipt)."""
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (width, height), color).save(buffer, "PNG")
    return buffer.getvalue()


RECEIPT_PNG = make_png()


def make_pdf(pages: int, title: str = "Testbuch") -> bytes:
    """A real PDF; every page carries the UNCOMPRESSED text `PAGEMARK<nnn>`, so a test can prove which pages a file contains."""
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pageCompression=0)
    pdf.setTitle(title)
    for i in range(1, pages + 1):
        pdf.drawString(72, 700, f"PAGEMARK{i:03d} Seite {i}")
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def ffmpeg(*args: str) -> None:
    subprocess.run([FFMPEG, "-nostdin", "-v", "error", "-y", *args], check=True)


class MedienBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DB_URL:
            raise unittest.SkipTest("integration test: set VIZU_WB_TEST_DB_URL (+ DATABASE_NAME)")
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import app.models  # noqa: F401
        from app.core.storage.protected_local import ProtectedMedienStorage
        from app.main import app
        from app.models.user import User

        cls.tmp = tempfile.TemporaryDirectory()
        cls.patch = patch.object(ProtectedMedienStorage, "ROOT", Path(cls.tmp.name) / "storage")
        cls.patch.start()
        cls.app, cls.client = app, TestClient(app)
        cls.tag = uuid.uuid4().hex[:6]
        cls.engine = create_engine(DB_URL)
        cls.sess = sessionmaker(bind=cls.engine, expire_on_commit=False)()
        cls.users = {}
        for name, role in (("a", "STUDENT"), ("b", "STUDENT"), ("rate", "STUDENT"), ("admin", "ADMIN"), ("super", "SUPER_ADMIN")):
            u = User(email=f"mb-{name}-{cls.tag}@test.local", username=f"mb_{name}_{cls.tag}", password_hash="x", is_active=True, is_verified=True,
                     is_superuser=role == "SUPER_ADMIN", role=role, is_banned=False, preferred_language="uz", first_name=name.title(), last_name="Tester")
            cls.sess.add(u)
            cls.users[name] = u
        cls.sess.commit()
        cls.extra_setup()

    @classmethod
    def extra_setup(cls):
        """Hook for subclasses."""

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import delete

        from app.api.dependencies.auth import get_current_user
        from app.models.audit_log import AuditLog
        from app.models.auth_rate_limit_event import AuthRateLimitEvent
        from app.models.medien import BookPaymentRequest, Film, MediaBook, MediaProgress, MediaPurchase, Song
        from app.models.user import User
        from app.services.auth import rate_limit

        cls.app.dependency_overrides.pop(get_current_user, None)
        ids = [u.id for u in cls.users.values()]
        s = cls.sess
        s.rollback()
        s.execute(delete(MediaPurchase).where(MediaPurchase.user_id.in_(ids)))
        s.execute(delete(BookPaymentRequest).where(BookPaymentRequest.user_id.in_(ids)))
        s.execute(delete(MediaProgress).where(MediaProgress.user_id.in_(ids)))
        for model in (MediaBook, Song, Film):
            s.execute(delete(model).where(model.title.like(f"T{cls.tag}%")))
        s.execute(delete(AuthRateLimitEvent).where(AuthRateLimitEvent.email_hash.in_([rate_limit._key("user", str(i)) for i in ids])))
        s.execute(delete(AuditLog).where(AuditLog.actor_id.in_([str(i) for i in ids])))
        s.execute(delete(User).where(User.id.in_(ids)))
        s.commit()
        s.close()
        cls.patch.stop()
        cls.tmp.cleanup()
        cls.engine.dispose()

    # ---------- helpers ----------
    def as_(self, who):
        from app.api.dependencies.auth import get_current_user

        if who is None:
            self.app.dependency_overrides.pop(get_current_user, None)
        else:
            self.app.dependency_overrides[get_current_user] = lambda: self.users[who]

    def api(self, method, url, who, expect=200, **kw):
        self.as_(who)
        r = getattr(self.client, method)(f"/api/v1{url}", **kw)
        if expect is not None:
            self.assertEqual(r.status_code, expect, f"{method.upper()} {url} -> {r.status_code} {r.text[:300]}")
        return r

    def title(self, name):
        return f"T{self.tag} {name}"

    def disk(self):
        root = Path(self.tmp.name) / "storage"
        return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} if root.exists() else set()

    def new_book(self, name, pages=15, pdf=True, **extra):
        body = {"title": self.title(name), "author": "Autor Eins", "language": "de", "level": "A2", "status": "PUBLISHED", **extra}
        book = self.api("post", "/admin/medien/books", "admin", json=body).json()
        if pdf:
            book = self.api("post", f"/admin/medien/books/{book['id']}/file", "admin", files={"file": ("b.pdf", make_pdf(pages, name), "application/pdf")}).json()
        return book

    def refresh(self, model, ident):
        self.sess.expire_all()
        return self.sess.get(model, uuid.UUID(str(ident)))
