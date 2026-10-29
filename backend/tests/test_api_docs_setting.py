"""/docs + /openapi.json were public in production (Swagger UI listing ~1000 endpoints)."""

import unittest

from app.core.config import Settings

BASE = {"SECRET_KEY": "x", "DATABASE_HOST": "h", "DATABASE_NAME": "d", "DATABASE_USER": "u", "DATABASE_PASSWORD": "p"}


def _settings(**kw):
    return Settings(_env_file=None, **BASE, **kw)


class TestApiDocsSetting(unittest.TestCase):
    def test_off_in_production_by_default(self):
        self.assertFalse(_settings(APP_ENV="production").API_DOCS)

    def test_on_outside_production(self):
        self.assertTrue(_settings(APP_ENV="development").API_DOCS)
        self.assertTrue(_settings(APP_ENV="test").API_DOCS)

    def test_explicit_switch_wins(self):
        self.assertTrue(_settings(APP_ENV="production", API_DOCS_ENABLED=True).API_DOCS)
        self.assertFalse(_settings(APP_ENV="development", API_DOCS_ENABLED=False).API_DOCS)


if __name__ == "__main__":
    unittest.main()
