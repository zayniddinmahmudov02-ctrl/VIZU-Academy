"""VIZU DEUTSCH mobile app releases: APK inspection (binary manifest, signer certificate, debug key), the API
contract (public download routes, Super-Admin-only admin routes, 401/403 over HTTP) without a database, and the
release rules (draft → publish → latest, version code must grow, same signer, archive, delete drafts only,
download counter) against PostgreSQL (VIZU_WB_TEST_DB_URL = a migrated test database)."""

import asyncio
import io
import os
import struct
import tempfile
import unittest
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

DB_URL = os.environ.get("VIZU_WB_TEST_DB_URL")


# ── fixtures: a minimal compiled AndroidManifest.xml + a v1 (PKCS#7) signature ──


def _axml(package: str, version_code: int, version_name: str, min_sdk: int = 24) -> bytes:
    strings = ["versionCode", "versionName", "minSdkVersion", "package", "manifest", "uses-sdk", package, version_name]
    res_map = [0x0101021B, 0x0101021C, 0x0101020C]
    body = b""
    offsets = []
    for s in strings:
        offsets.append(len(body))
        body += struct.pack("<H", len(s)) + s.encode("utf-16-le") + b"\0\0"
    body += b"\0" * (-len(body) % 4)
    header = 28
    pool = struct.pack("<HHIIIIII", 0x0001, header, header + 4 * len(strings) + len(body), len(strings), 0, 0,
                       header + 4 * len(strings), 0) + struct.pack(f"<{len(strings)}I", *offsets) + body
    resmap = struct.pack("<HHI", 0x0180, 8, 8 + 4 * len(res_map)) + struct.pack(f"<{len(res_map)}I", *res_map)

    def attr(name_i, raw, dtype, data):
        return struct.pack("<IIIHBBI", 0xFFFFFFFF, name_i, raw, 8, 0, dtype, data)

    def element(name_i, attrs):
        ext = struct.pack("<IIHHHHHH", 0xFFFFFFFF, name_i, 20, 20, len(attrs), 0, 0, 0)
        payload = struct.pack("<II", 1, 0xFFFFFFFF) + ext + b"".join(attrs)
        return struct.pack("<HHI", 0x0102, 16, 8 + len(payload)) + payload

    manifest = element(4, [attr(3, 6, 0x03, 6), attr(0, 0xFFFFFFFF, 0x10, version_code), attr(1, 7, 0x03, 7)])
    uses_sdk = element(5, [attr(2, 0xFFFFFFFF, 0x10, min_sdk)])
    tree = pool + resmap + manifest + uses_sdk
    return struct.pack("<HHI", 0x0003, 8, 8 + len(tree)) + tree


def _cert_pkcs7(common_name: str) -> bytes:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import pkcs7
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=3650)).sign(key, hashes.SHA256()))
    return (pkcs7.PKCS7SignatureBuilder().set_data(b"MANIFEST").add_signer(cert, key, hashes.SHA256())
            .sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature]))


_SIGNERS: dict[str, bytes] = {}


def _apk(version_code=2, version_name="1.1.0", package="com.vizu.deutsch", signer="VIZU Release", signed=True) -> bytes:
    if signed and signer not in _SIGNERS:
        _SIGNERS[signer] = _cert_pkcs7(signer)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as zf:
        zf.writestr("AndroidManifest.xml", _axml(package, version_code, version_name))
        zf.writestr("classes.dex", b"dex\n035\0")
        if signed:
            zf.writestr("META-INF/CERT.RSA", _SIGNERS[signer])
    return out.getvalue()


def _write(data: bytes) -> Path:
    fd, name = tempfile.mkstemp(suffix=".apk")
    os.write(fd, data)
    os.close(fd)
    return Path(name)


class TestApkInspection(unittest.TestCase):
    def setUp(self):
        self.files = []

    def tearDown(self):
        for f in self.files:
            f.unlink(missing_ok=True)

    def _inspect(self, data):
        from app.services.app_releases.apk import inspect_apk

        p = _write(data)
        self.files.append(p)
        return inspect_apk(p)

    def test_reads_manifest_and_signer(self):
        info = self._inspect(_apk(version_code=7, version_name="1.4.2"))
        self.assertEqual((info.package, info.version_code, info.version_name, info.min_sdk), ("com.vizu.deutsch", 7, "1.4.2", 24))
        self.assertEqual(len(info.signer_sha256), 64)
        self.assertFalse(info.debug_signed)
        self.assertEqual(len(info.sha256), 64)

    def test_same_key_same_fingerprint_other_key_differs(self):
        a = self._inspect(_apk(version_code=1)).signer_sha256
        b = self._inspect(_apk(version_code=2)).signer_sha256
        c = self._inspect(_apk(version_code=3, signer="Somebody Else")).signer_sha256
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_debug_certificate_is_detected(self):
        self.assertTrue(self._inspect(_apk(signer="Android Debug")).debug_signed)

    def test_rejects_unsigned_broken_and_non_apk(self):
        from app.services.app_releases.apk import ApkError

        for data, code in ((_apk(signed=False), "APK_NOT_SIGNED"), (b"not a zip at all", "APK_INVALID")):
            with self.subTest(code=code), self.assertRaises(ApkError) as ctx:
                self._inspect(data)
            self.assertEqual(ctx.exception.code, code)
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as zf:
            zf.writestr("AndroidManifest.xml", b"\x03\x00\x08\x00garbage")
            zf.writestr("classes.dex", b"x")
        with self.assertRaises(ApkError) as ctx:
            self._inspect(out.getvalue())
        self.assertEqual(ctx.exception.code, "APK_INVALID_MANIFEST")

    def test_android_version_label(self):
        from app.services.app_releases.service import android_version

        self.assertEqual(android_version(24), "7.0")
        self.assertEqual(android_version(35), "15")


class TestApiContract(unittest.TestCase):
    def test_admin_routes_are_super_admin_only(self):
        from app.api.app_releases.router import admin_router
        from app.api.dependencies.auth import require_super_admin

        for r in admin_router.routes:
            with self.subTest(route=r.path, methods=r.methods):
                self.assertIn(require_super_admin, [d.call for d in r.dependant.dependencies])

    def test_public_routes_carry_no_user(self):
        from app.api.app_releases.router import router
        from app.db.session import get_db

        for r in router.routes:
            with self.subTest(route=r.path):
                self.assertLessEqual({d.call for d in r.dependant.dependencies}, {get_db})

    def test_mounted_under_api_v1(self):
        from app.main import app

        paths = set(app.openapi()["paths"])
        for p in ("/api/v1/app/releases/latest", "/api/v1/app/android/latest.apk", "/api/v1/app/download-qr.svg",
                  "/api/v1/admin/app-releases", "/api/v1/admin/app-releases/{release_id}/publish"):
            self.assertIn(p, paths)

    def test_notes_body_rejects_extra_fields(self):
        from pydantic import ValidationError

        from app.api.app_releases.router import NotesIn

        with self.assertRaises(ValidationError):
            NotesIn(release_notes="x", status="published")

    def test_qr_svg_points_at_download_page(self):
        from app.services.app_releases.service import qr_svg

        svg = qr_svg()
        self.assertTrue(svg.lstrip().startswith("<"))
        self.assertIn("svg", svg[:200])

    def test_http_401_and_403(self):
        try:
            from fastapi.testclient import TestClient
        except Exception:  # httpx missing (server)
            self.skipTest("httpx not installed")
        from app.api.dependencies.auth import get_current_user
        from app.main import app
        from types import SimpleNamespace

        client = TestClient(app)
        self.assertEqual(client.get("/api/v1/admin/app-releases").status_code, 401)
        self.assertEqual(client.post("/api/v1/admin/app-releases", files={"file": ("a.apk", b"x")}).status_code, 401)
        for role in ("ADMIN", "CONTENT_MANAGER", "STUDENT"):
            app.dependency_overrides[get_current_user] = lambda role=role: SimpleNamespace(id=uuid.uuid4(), role=role)
            try:
                with self.subTest(role=role):
                    self.assertEqual(client.get("/api/v1/admin/app-releases").status_code, 403)
                    self.assertEqual(client.post(f"/api/v1/admin/app-releases/{uuid.uuid4()}/publish").status_code, 403)
            finally:
                app.dependency_overrides.pop(get_current_user, None)


@unittest.skipUnless(DB_URL, "integration test: set VIZU_WB_TEST_DB_URL to a migrated test database")
class TestReleaseRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.models.user import User

        cls.engine = create_engine(DB_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        db = cls.Session()
        tag = uuid.uuid4().hex[:6]
        admin = User(email=f"ar-admin-{tag}@test.local", username=f"ar_admin_{tag}", password_hash="x", is_active=True,
                     is_verified=True, is_superuser=True, role="SUPER_ADMIN", is_banned=False, preferred_language="uz")
        db.add(admin)
        db.commit()
        cls.admin_id = admin.id
        db.close()

    @classmethod
    def tearDownClass(cls):
        from sqlalchemy import text

        with cls.engine.begin() as c:
            c.execute(text("DELETE FROM app_releases"))
        cls.engine.dispose()

    def setUp(self):
        from sqlalchemy import text

        from app.models.user import User
        from app.services.app_releases import service

        self.tmp = tempfile.TemporaryDirectory()
        self.patch = patch.object(type(service.storage), "ROOT", Path(self.tmp.name))
        self.patch.start()
        self.db = self.Session()
        self.db.execute(text("DELETE FROM app_releases"))
        self.db.commit()
        self.admin = self.db.get(User, self.admin_id)
        self.service = service

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        self.patch.stop()
        self.tmp.cleanup()

    def _upload(self, data, name="vizu.apk", notes="Neu", content_type="application/vnd.android.package-archive"):
        from starlette.datastructures import Headers, UploadFile

        f = UploadFile(io.BytesIO(data), filename=name, headers=Headers({"content-type": content_type}))
        return asyncio.run(self.service.upload(self.db, self.admin, f, notes))

    def _code(self, fn, *args):
        with self.assertRaises(HTTPException) as ctx:
            fn(*args)
        return str(ctx.exception.detail).split(":")[0]

    def test_draft_publish_latest_download(self):
        r = self._upload(_apk(version_code=2, version_name="1.1.0"))
        self.assertEqual((r["status"], r["version_code"], r["version_name"], r["min_android_version"]), ("draft", 2, "1.1.0", "7.0"))
        self.assertEqual(self._code(self.service.latest_or_404, self.db), "NO_APP_RELEASE")
        p = self.service.publish(self.db, self.admin, uuid.UUID(r["id"]))
        self.assertTrue(p["is_latest"])
        latest = self.service.latest_or_404(self.db)
        path = self.service.register_download(self.db, latest)
        self.assertTrue(path.is_file())
        self.db.refresh(latest)
        self.assertEqual(latest.download_count, 1)
        self.assertEqual(self.service.public_view(latest)["download_url"], "/api/v1/app/android/latest.apk")
        self.assertNotIn("storage_name", self.service.public_view(latest))

    def test_newer_release_takes_over_and_version_must_grow(self):
        a = self._upload(_apk(version_code=2))
        self.service.publish(self.db, self.admin, uuid.UUID(a["id"]))
        b = self._upload(_apk(version_code=3, version_name="1.2.0"))
        self.service.publish(self.db, self.admin, uuid.UUID(b["id"]))
        rows = {x["version_code"]: x for x in self.service.list_releases(self.db)["releases"]}
        self.assertEqual((rows[2]["is_latest"], rows[3]["is_latest"]), (False, True))
        old = self._upload(_apk(version_code=1, version_name="1.0.0"))
        self.assertEqual(self._code(self.service.publish, self.db, self.admin, uuid.UUID(old["id"])), "VERSION_CODE_NOT_NEWER")
        self.assertEqual(self._code(self._upload, _apk(version_code=3)), "APK_VERSION_EXISTS")

    def test_upload_refusals(self):
        a = self._upload(_apk(version_code=2))
        self.service.publish(self.db, self.admin, uuid.UUID(a["id"]))
        cases = {
            "APK_SIGNER_MISMATCH": dict(data=_apk(version_code=5, signer="Other Key")),
            "APK_DEBUG_SIGNED": dict(data=_apk(version_code=6, signer="Android Debug")),
            "APK_WRONG_PACKAGE": dict(data=_apk(version_code=7, package="com.evil.app")),
            "APK_NOT_SIGNED": dict(data=_apk(version_code=8, signed=False)),
            "APK_EXTENSION": dict(data=_apk(version_code=9), name="vizu.zip"),
            "APK_MIME_TYPE": dict(data=_apk(version_code=10), content_type="text/html"),
        }
        for code, kw in cases.items():
            with self.subTest(code=code):
                self.assertEqual(self._code(lambda: self._upload(**kw)), code)
        self.assertEqual(len(list(Path(self.tmp.name).iterdir())), 1, "refused uploads leave no file behind")

    def test_archive_and_delete_rules(self):
        a = self._upload(_apk(version_code=2))
        self.assertEqual(self._code(self.service.archive, self.db, self.admin, uuid.UUID(a["id"])), "APP_RELEASE_DRAFT")
        self.service.publish(self.db, self.admin, uuid.UUID(a["id"]))
        self.assertEqual(self._code(self.service.delete_draft, self.db, self.admin, uuid.UUID(a["id"])), "APP_RELEASE_NOT_DRAFT")
        arch = self.service.archive(self.db, self.admin, uuid.UUID(a["id"]))
        self.assertEqual((arch["status"], arch["is_latest"]), ("archived", False))
        self.assertEqual(self._code(self.service.latest_or_404, self.db), "NO_APP_RELEASE")
        d = self._upload(_apk(version_code=4))
        self.service.delete_draft(self.db, self.admin, uuid.UUID(d["id"]))
        self.assertEqual({x["version_code"] for x in self.service.list_releases(self.db)["releases"]}, {2})


if __name__ == "__main__":
    unittest.main()
