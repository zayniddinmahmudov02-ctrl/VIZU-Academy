"""Declared A2 audio assets for Unterricht 1–13.

This manifest describes expected source files only. It never creates lessons,
tasks, questions, answer keys, or audio records.
"""

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class A2AudioMaterial:
    lesson_number: int
    material_number: int
    source_name: str
    extension: str
    key: str


def _lesson(lesson_number: int, names: list[tuple[str, str]]) -> list[A2AudioMaterial]:
    return [
        A2AudioMaterial(
            lesson_number=lesson_number,
            material_number=index,
            source_name=name,
            extension=extension,
            key=f"a2-l{lesson_number:02d}-audio-{index:02d}",
        )
        for index, (name, extension) in enumerate(names, start=1)
    ]


A2_AUDIO_MATERIALS = tuple(
    material
    for lesson_number, files in (
        (1, [("A2 1.Unterricht Hören", "m4a")]),
        (2, [("A2 2.Unterricht Hören", "mp3")]),
        (3, [("A2. 3.Unterricht Hören", "mp3")]),
        (4, [(f"A2 4.Unterricht Text {i}", "mp3") for i in range(1, 4)]),
        (5, [("A2 5.Unterricht Hören", "mp3")]),
        (6, [("A2 6.Unterricht", "mp3")]),
        (7, [(f"A2 7.Unterricht Text {i}", "mp3") for i in range(1, 3)]),
        (8, [("A2 8.Unterricht", "mp3")]),
        (9, [("A2 9.Unterricht Hören", "mp3")]),
        (10, [(f"A2 10.Unterricht Teil {i}", "m4a") for i in range(1, 5)]),
        (11, [(f"A2 11.Unterricht Teil_{i}", "m4a") for i in range(1, 5)]),
        (12, [(f"A2 12.Unterricht Teil_{i}", "m4a") for i in range(1, 5)]),
        (13, [(f"A2 13.Unterricht Teil {i}", "m4a") for i in range(1, 5)]),
    )
    for material in _lesson(lesson_number, files)
)


def normalize_filename(value: str) -> str:
    name = Path(value).name
    name = re.sub(r"\.(?:mp3|m4a)$", "", name, flags=re.IGNORECASE)
    return re.sub(r"[^a-z0-9]", "", name.casefold())


def audit_audio_files(paths: list[Path]) -> dict:
    """Compare discovered MP3/M4A files with the 28 declared source assets."""
    audio_paths = sorted(
        (path for path in paths if path.suffix.casefold() in {".mp3", ".m4a"}),
        key=lambda path: str(path).casefold(),
    )
    by_name: dict[str, list[Path]] = {}
    for path in audio_paths:
        by_name.setdefault(normalize_filename(path.name), []).append(path)

    matched = []
    missing = []
    ambiguous = []
    wrong_format = []
    for material in A2_AUDIO_MATERIALS:
        candidates = by_name.get(normalize_filename(material.source_name), [])
        if not candidates:
            missing.append(material)
            continue
        if len(candidates) > 1:
            ambiguous.append({"material": material, "files": candidates})
            continue
        candidate = candidates[0]
        if candidate.suffix.casefold() != f".{material.extension}":
            wrong_format.append(
                {"material": material, "file": candidate, "expected_extension": material.extension}
            )
            continue
        matched.append({"material": material, "file": candidate})

    expected_names = {normalize_filename(material.source_name) for material in A2_AUDIO_MATERIALS}
    unexpected = [path for path in audio_paths if normalize_filename(path.name) not in expected_names]
    return {
        "expected_count": len(A2_AUDIO_MATERIALS),
        "discovered_count": len(audio_paths),
        "matched_count": len(matched),
        "missing": missing,
        "ambiguous": ambiguous,
        "wrong_format": wrong_format,
        "unexpected": unexpected,
        "ok": (
            len(matched) == len(A2_AUDIO_MATERIALS)
            and not missing
            and not ambiguous
            and not wrong_format
            and not unexpected
        ),
    }
