"""Migration a7c4e2f9b1d8 (Multilevel Premium entitlements, promo approval + category, course promo requests): upgrade -> downgrade -> upgrade
on a throwaway database (VIZU_MIGRATION_TEST_DB_URL, at head). Existing promo codes keep working (active -> ACTIVE + approved, inactive ->
DISABLED, package-only -> PACKAGES), existing requests become CODE_APPROVAL, the new table / columns appear and disappear, one active
entitlement per student and product."""

import os
import unittest
import uuid

DB_URL = os.environ.get("VIZU_MIGRATION_TEST_DB_URL")
REV, PREVIOUS_REV = "a7c4e2f9b1d8", "e6d2b9a4c8f3"


@unittest.skipUnless(DB_URL, "migration test: set VIZU_MIGRATION_TEST_DB_URL to a dedicated database at head")
class TestMultilevelPremiumMigration(unittest.TestCase):
    def setUp(self):
        from pathlib import Path

        from alembic.config import Config
        from sqlalchemy import create_engine

        root = Path(__file__).resolve().parents[1]
        self.cfg = Config()
        self.cfg.set_main_option("script_location", str(root / "alembic"))
        self.engine = create_engine(DB_URL)

    def tearDown(self):
        self._alembic("upgrade", "head")
        self.engine.dispose()

    def _alembic(self, action: str, revision: str) -> None:
        from unittest.mock import patch

        from alembic import command
        from sqlalchemy.engine import make_url

        from app.core.config import settings

        url = make_url(DB_URL)
        with patch.multiple(settings, DATABASE_HOST=url.host, DATABASE_PORT=url.port or 5432, DATABASE_NAME=url.database,
                            DATABASE_USER=url.username, DATABASE_PASSWORD=url.password or ""):
            getattr(command, action)(self.cfg, revision)

    def _q(self, sql, **params):
        from sqlalchemy import text

        with self.engine.begin() as c:
            result = c.execute(text(sql), params)
            return result.fetchall() if result.returns_rows else []

    def _table(self):
        return bool(self._q("SELECT 1 FROM information_schema.tables WHERE table_name = 'user_entitlements'"))

    def _columns(self, table):
        return {r[0] for r in self._q("SELECT column_name FROM information_schema.columns WHERE table_name = :t", t=table)}

    def test_upgrade_downgrade_upgrade_keeps_codes_working(self):
        from sqlalchemy.orm import Session

        import app.models  # noqa: F401
        from app.models.user import User

        tag = uuid.uuid4().hex[:6].upper()
        with Session(self.engine) as db:  # the users table is not touched by this migration
            user = User(email=f"mig-{tag.lower()}@test.local", username=f"mig_{tag.lower()}", password_hash="x", is_active=True, is_verified=True,
                        is_superuser=True, role="SUPER_ADMIN", is_banned=False, preferred_language="uz")
            db.add(user)
            db.commit()
            user_id = user.id
        codes = {"active": f"MIGA{tag}", "inactive": f"MIGI{tag}", "package": f"MIGP{tag}"}
        try:
            self._alembic("downgrade", PREVIOUS_REV)
            self.assertFalse(self._table())
            self.assertTrue({"product_category", "approval_status", "assigned_user_id"}.isdisjoint(self._columns("promo_codes")))
            self.assertTrue({"paid_at", "no_receipt", "student_note", "admin_note"}.isdisjoint(self._columns("subscription_orders")))
            for key, active, courses, packages in (("active", True, '["c1"]', "[]"), ("inactive", False, '["c1"]', "[]"),
                                                   ("package", True, "[]", '["A1_B1"]')):
                self._q("INSERT INTO promo_codes (id, code, discount_type, discount_value, used_count, max_uses_per_user, applicable_course_ids,"
                        " applicable_package_codes, requires_approval, is_active, created_by_id, created_at, updated_at) VALUES (:i, :c, 'FREE_ACCESS',"
                        " 100, 3, 1, CAST(:cs AS jsonb), CAST(:ps AS jsonb), false, :a, :u, now(), now())",
                        i=uuid.uuid4(), c=codes[key], cs=courses, ps=packages, a=active, u=user_id)

            self._alembic("upgrade", REV)
            self.assertTrue(self._table())
            rows = {r[0]: r[1:] for r in self._q(
                "SELECT code, approval_status, product_category, is_active, approved_at IS NOT NULL, approved_by_id, used_count, review_note IS NOT NULL"
                " FROM promo_codes WHERE code = ANY(:c)", c=list(codes.values()))}
            self.assertEqual(rows[codes["active"]], ("ACTIVE", "COURSES", True, True, user_id, 3, True))
            self.assertEqual(rows[codes["inactive"]][:3], ("DISABLED", "COURSES", False))
            self.assertEqual(rows[codes["package"]][:2], ("ACTIVE", "PACKAGES"))
            # a new code defaults to PENDING (never usable without an approval)
            self._q("INSERT INTO promo_codes (id, code, discount_type, discount_value, used_count, max_uses_per_user, applicable_course_ids,"
                    " applicable_package_codes, requires_approval, is_active, created_at, updated_at) VALUES (:i, :c, 'PERCENT', 10, 0, 1, '[]', '[]',"
                    " false, false, now(), now())", i=uuid.uuid4(), c=f"MIGN{tag}")
            self.assertEqual(self._q("SELECT approval_status FROM promo_codes WHERE code = :c", c=f"MIGN{tag}"), [("PENDING",)])
            with self.assertRaises(Exception):
                self._q("UPDATE promo_codes SET approval_status = 'WHATEVER' WHERE code = :c", c=f"MIGN{tag}")
            # one active entitlement per student and product
            ins = ("INSERT INTO user_entitlements (id, user_id, product, source, granted_at, created_at, updated_at)"
                   " VALUES (:i, :u, 'MULTILEVEL_MODELLTEST_PREMIUM', 'PAYMENT', now(), now(), now())")
            first = uuid.uuid4()
            self._q(ins, i=first, u=user_id)
            with self.assertRaises(Exception):
                self._q(ins, i=uuid.uuid4(), u=user_id)
            self._q("UPDATE user_entitlements SET revoked_at = now() WHERE id = :i", i=first)
            self._q(ins, i=uuid.uuid4(), u=user_id)  # after a refund (revoked) a new one is allowed
            # a course promo request needs no code; a code-approval request still does
            self._q("INSERT INTO promo_code_requests (id, user_id, plan, status, kind, created_at, updated_at) VALUES (:i, :u, 'A1', 'PENDING_APPROVAL',"
                    " 'COURSE_REQUEST', now(), now())", i=uuid.uuid4(), u=user_id)
            with self.assertRaises(Exception):
                self._q("INSERT INTO promo_code_requests (id, user_id, plan, status, created_at, updated_at) VALUES (:i, :u, 'A1', 'PENDING_APPROVAL',"
                        " now(), now())", i=uuid.uuid4(), u=user_id)

            self._alembic("downgrade", PREVIOUS_REV)  # course requests without a code go, everything else stays
            self.assertFalse(self._table())
            self.assertEqual(self._q("SELECT count(*) FROM promo_code_requests WHERE user_id = :u", u=user_id), [(0,)])
            self.assertEqual(self._q("SELECT count(*) FROM promo_codes WHERE code = ANY(:c)", c=list(codes.values())), [(3,)])
            self._alembic("upgrade", REV)
        finally:
            self._alembic("upgrade", "head")
            self._q("DELETE FROM promo_codes WHERE code LIKE :p", p=f"MIG_{tag}".replace("_", "%"))
            self._q("DELETE FROM users WHERE id = :u", u=user_id)


if __name__ == "__main__":
    unittest.main()
