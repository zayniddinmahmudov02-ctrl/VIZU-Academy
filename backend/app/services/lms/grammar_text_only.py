"""Grammatik is text only in the VIZU-DEUTSCH book levels.

The book's grammar is taught as text, tables and examples. Old posters and
scanned book pages (e.g. "Deutsche Alphabet / Nemis tili alifbosi") must not
reach students, whatever the data says:

* the student lesson API drops IMAGE resources of the Grammatik competency
  and the images embedded in the Grammatik competency text;
* the student grammar API drops images embedded in the grammar rules;
* the admin API refuses to attach a new image to Grammatik.

The data itself is cleaned by `import_vizu_deutsch_a1 --replace` or
`--remove-grammar-images` (archived first). Other levels are unchanged.
"""

import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.lesson import Lesson
from app.services.lms import structure

TEXT_ONLY_LEVELS = frozenset({"A1"})
GRAMMATIK = "GRAMMATIK"

# an image in admin / book HTML, with an optional wrapping <figure>
_IMG = re.compile(r"<figure\b[^>]*>\s*<img\b[^>]*>.*?</figure>|<img\b[^>]*>", re.IGNORECASE | re.DOTALL)
_EMPTY_P = re.compile(r"<p\b[^>]*>\s*(?:<br\s*/?>\s*)*</p>", re.IGNORECASE)


def has_images(html: str | None) -> bool:
    return bool(html and _IMG.search(html))


def strip_images(html: str) -> str:
    """The HTML without its images (and the paragraphs that held nothing but
    an image); the text stays."""
    return _EMPTY_P.sub("", _IMG.sub("", html)).strip()


def applies(db: Session, lesson: Lesson | None) -> bool:
    if lesson is None:
        return False
    course, _ = structure.lesson_level(db, lesson)
    return bool(course and course.level in TEXT_ONLY_LEVELS)


def is_grammar_image(resource) -> bool:
    return resource.competency == GRAMMATIK and resource.resource_type == "IMAGE"


def ensure_resource_allowed(db: Session, lesson: Lesson, resource_type: str | None, competency: str | None) -> None:
    if (competency or "").strip().upper() == GRAMMATIK and (resource_type or "").strip().upper() == "IMAGE" and applies(db, lesson):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="GRAMMATIK_TEXT_ONLY: Grammatik uchun rasm yuklanmaydi — qoidalarni matn va jadval ko'rinishida kiriting.",
        )
