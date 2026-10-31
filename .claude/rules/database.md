---
paths:
  - "backend/app/models/**"
  - "backend/alembic/**"
---
# Database rules

Map and current head: `docs/ai-context/database-map.md`.

- One linear Alembic history. New migration: `down_revision` = current head, a module docstring that says
  what it adds and what downgrade does, additive where possible (new column nullable / new table).
- Write a migration test: upgrade → downgrade → upgrade on the dedicated DB
  (`VIZU_MIGRATION_TEST_DB_URL`), pattern `tests/test_listening_task_key_migration.py`
  (`alembic.config.Config()` without the ini file + `patch.multiple(settings, DATABASE_*)`).
- Indexes / constraints declared in the model `__table_args__` too (same names as the migration).
- Production: preview the SQL with `alembic upgrade <cur>:head --sql`, stop if the current revision or the
  number of heads is unexpected, take the backup first. Never downgrade production automatically.
- Deleting rows: only with a backup of the rows (JSON) and when no learner history depends on them;
  `lesson_skill_attempts` cascade from `listenings` — archive tasks (`[Archiv]`, unpublished) instead.
