"""Bootstrap script: ensures the platform's one seeded language (German)
exists with the correct field values, per the Enterprise Language
Management module spec.

Idempotent — if a language with code "de" already exists (it does, from
before this module existed), its fields are updated to match rather than
inserting a duplicate. Also guarantees exactly one language is marked
is_default (unsetting any other row that might have it).

Run from the `backend/` directory:

    python -m app.scripts.seed_default_language
"""

import app.models  # noqa: F401 — registers every model with Base before querying

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.language import Language
from app.models.language_settings import LanguageSettings

CODE = "de"
LOCALE = "de-DE"
NAME = "Deutsch"
NATIVE_NAME = "Deutsch"
ENGLISH_NAME = "German"
FLAG_FILE = "de.svg"


def main() -> None:
    db = SessionLocal()

    try:
        language = db.scalar(
            select(Language).where(Language.code == CODE, Language.deleted_at.is_(None))
        )

        if language is None:
            language = Language(code=CODE)
            db.add(language)
            print("Creating new language row for code='de'.")
        else:
            print(f"Updating existing language row {language.id} for code='de'.")

        language.locale = LOCALE
        language.name = NAME
        language.native_name = NATIVE_NAME
        language.english_name = ENGLISH_NAME
        language.flag_file = FLAG_FILE
        language.is_default = True
        language.is_active = True
        if not language.sort_order:
            language.sort_order = 1

        db.flush()

        # Exactly one default language, platform-wide.
        db.query(Language).filter(Language.id != language.id, Language.is_default.is_(True)).update(
            {"is_default": False}
        )

        existing_settings = db.scalar(
            select(LanguageSettings).where(LanguageSettings.language_id == language.id)
        )
        if existing_settings is None:
            db.add(LanguageSettings(language_id=language.id))
            print("Creating default LanguageSettings row (all features enabled).")

        db.commit()
        print(f"Done. Language: id={language.id} code={language.code} locale={language.locale} is_default={language.is_default}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
