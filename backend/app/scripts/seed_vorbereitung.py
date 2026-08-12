"""Bootstrap script: seeds the Vorbereitung structural hierarchy
(CertificationProvider -> MockExamLevel -> ModelTest) from the providers
and levels already shown on the public site (frontend/src/constants/
exams.ts) — that file is the source of truth for which provider/level
combinations are valid; this script does not invent any.

Idempotent and additive only:
  - A provider already existing by `code` is left untouched (never
    duplicated, never overwritten).
  - A level already existing for (provider, level) is left untouched.
  - Each valid (provider, level) combination is topped up to exactly 10
    ModelTests: existing ones are counted and never duplicated, and only
    the missing ones are created titled "Modelltest N" continuing from
    the current count. If more than 10 already exist, nothing is
    deleted — the discrepancy is only reported.
  - Every created ModelTest starts as DRAFT with empty Kompetenzen —
    no fake competency content is ever created here.

Run from the `backend/` directory:

    python -m app.scripts.seed_vorbereitung
"""

import app.models  # noqa: F401 — registers every model with Base before querying

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.certification_provider import CertificationProvider
from app.models.mock_exam_level import MockExamLevel
from app.models.model_test import ModelTest

TARGET_MODEL_TESTS_PER_LEVEL = 10

# Mirrors frontend/src/constants/exams.ts `examProviders` exactly —
# provider code, display name, description, accent color, and the CEFR
# levels each one actually supports on the public site today.
PROVIDERS = [
    {
        "code": "GOETHE",
        "name": "Goethe-Zertifikat",
        "description": "Goethe-Institut",
        "color": "#3b82f6",
        "levels": ["A1", "A2", "B1", "B2", "C1"],
    },
    {
        "code": "TELC",
        "name": "telc Deutsch",
        "description": "The European Language Certificates",
        "color": "#22c55e",
        "levels": ["A1", "A2", "B1", "B2", "C1"],
    },
    {
        "code": "OESD",
        "name": "ÖSD Zertifikat",
        "description": "Österreichisches Sprachdiplom",
        "color": "#f59e0b",
        "levels": ["A1", "A2", "B1", "B2", "C1"],
    },
    {
        "code": "TESTDAF",
        "name": "TestDaF",
        "description": "Test Deutsch als Fremdsprache",
        "color": "#1e3a8a",
        "levels": ["B2", "C1"],
    },
]


def main() -> None:
    db = SessionLocal()
    created_providers = 0
    created_levels = 0
    created_model_tests = 0
    over_target: list[str] = []

    try:
        for sort_index, provider_data in enumerate(PROVIDERS, start=1):
            provider = db.scalar(
                select(CertificationProvider).where(CertificationProvider.code == provider_data["code"])
            )
            if provider is None:
                provider = CertificationProvider(
                    name=provider_data["name"],
                    code=provider_data["code"],
                    description=provider_data["description"],
                    color=provider_data["color"],
                    is_active=True,
                    sort_order=sort_index,
                )
                db.add(provider)
                db.flush()
                created_providers += 1
                print(f"Created provider: {provider.name} ({provider.code})")
            else:
                print(f"Provider already exists: {provider.name} ({provider.code}) — left untouched.")

            for level_sort, level_code in enumerate(provider_data["levels"], start=1):
                level = db.scalar(
                    select(MockExamLevel).where(
                        MockExamLevel.provider_id == provider.id,
                        MockExamLevel.level == level_code,
                    )
                )
                if level is None:
                    level = MockExamLevel(
                        provider_id=provider.id,
                        level=level_code,
                        sort_order=level_sort,
                        is_active=True,
                    )
                    db.add(level)
                    db.flush()
                    created_levels += 1
                    print(f"  Created level: {provider.code} {level_code}")
                else:
                    print(f"  Level already exists: {provider.code} {level_code} — left untouched.")

                existing_count = db.scalar(
                    select(func.count()).select_from(ModelTest).where(ModelTest.level_id == level.id)
                )

                if existing_count > TARGET_MODEL_TESTS_PER_LEVEL:
                    msg = (
                        f"    DISCREPANCY: {provider.code} {level_code} has "
                        f"{existing_count} Modelltests, more than the target of "
                        f"{TARGET_MODEL_TESTS_PER_LEVEL}. Not deleting anything — review manually."
                    )
                    print(msg)
                    over_target.append(f"{provider.code} {level_code}: {existing_count}")
                    continue

                if existing_count == TARGET_MODEL_TESTS_PER_LEVEL:
                    print(f"    {provider.code} {level_code} already has exactly {TARGET_MODEL_TESTS_PER_LEVEL} Modelltests — skipping.")
                    continue

                missing = TARGET_MODEL_TESTS_PER_LEVEL - existing_count
                for i in range(missing):
                    n = existing_count + i + 1
                    db.add(
                        ModelTest(
                            level_id=level.id,
                            title=f"Modelltest {n}",
                            status="DRAFT",
                            sort_order=n,
                        )
                    )
                    created_model_tests += 1
                print(f"    Created {missing} Modelltest(s) for {provider.code} {level_code} (had {existing_count}).")

        db.commit()

        print()
        print("Done.")
        print(f"Providers created: {created_providers}")
        print(f"Levels created: {created_levels}")
        print(f"ModelTests created: {created_model_tests}")
        if over_target:
            print("Discrepancies found (more than 10 existing, not touched):")
            for line in over_target:
                print(f"  - {line}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
