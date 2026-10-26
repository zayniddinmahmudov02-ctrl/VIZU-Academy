"""A2 6. Unterricht — book-faithful edition (see package docstring)."""

from . import IMAGES as _IMAGES, items as _items, lesson_description, lesson_title

N = 6
LESSON_TITLE = lesson_title(N)
LESSON_DESCRIPTION = lesson_description(N)
AUDIO: dict = {}  # audio is uploaded by an admin in Media Management
IMAGES = _IMAGES.get(N, [])


def items() -> list[dict]:
    return _items(N)