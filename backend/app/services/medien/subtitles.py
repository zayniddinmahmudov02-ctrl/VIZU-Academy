"""Subtitle files of Medienwelt films: decode, parse (WebVTT / SubRip), check, sanitise and normalise.

Nothing here touches the database or the disk, so it is unit-tested on its own (`tests/test_medien_subtitles.py`).

Rules
  * Input: UTF-8 (with or without BOM), UTF-16 with BOM, or Windows-1252 (German `.srt` files often are; reported as a warning).
    Binary files (NUL bytes), empty files and files without a single valid cue are refused (`SubtitleError`).
  * Parsing is tolerant: a broken block is skipped and counted as a warning, the rest is kept. Cues are sorted by start time.
  * Text is plain text only: every tag (`<i>`, `<font>`, `<v Name>`, inline timestamps, scripts …) is removed, HTML entities are
    decoded, control characters are dropped, long text is cut. The normalised file escapes `& < >` again, so it can never carry
    markup. The player draws the text itself (React escapes it) — the browser's own track parser is not used.
  * Checks against the video: a subtitle that ends far after the video, or long before it, is reported (warnings, never a crash).
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

MAX_CUES = 20_000
MAX_CUE_TEXT = 500
MAX_LINE = 84  # characters per line before "long line" is counted
MAX_DAY_MS = 24 * 3600 * 1000
PREVIEW_CUES = 30

_TS = r"(?:(\d{1,3}):)?(\d{1,2}):(\d{2})[.,](\d{1,3})"
_ARROW = re.compile(rf"^\s*{_TS}\s*-->\s*{_TS}(?:\s.*)?$")
_ARROW_LOOSE = re.compile(r"-->")
_TAG = re.compile(r"<[^>]*>")
_BR = re.compile(r"<br\s*/?>", re.I)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f​-‏‪-‮⁦-⁩﻿]")
_SPACES = re.compile(r"[ \t ]+")


class SubtitleError(ValueError):
    """The file cannot be used. `code` is an UPPER_SNAKE error code, `args[0]` the German-neutral English message."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class Cue:
    start: int  # ms
    end: int  # ms
    text: str  # plain text, lines joined with "\n"


@dataclass
class Analysis:
    cues: list[Cue]
    format: str  # "vtt" | "srt"
    encoding: str
    warnings: list[dict] = field(default_factory=list)

    @property
    def first_ms(self) -> int | None:
        return self.cues[0].start if self.cues else None

    @property
    def last_ms(self) -> int | None:
        return max((c.end for c in self.cues), default=None)

    def report(self) -> dict:
        return {"format": self.format, "encoding": self.encoding, "cue_count": len(self.cues), "first_ms": self.first_ms,
                "last_ms": self.last_ms, "warnings": self.warnings}


def _warn(warnings: list[dict], code: str, detail: str, count: int = 1) -> None:
    for w in warnings:
        if w["code"] == code:
            w["count"] += count
            return
    warnings.append({"code": code, "count": count, "detail": detail})


# ---------------- decoding ----------------


def decode(raw: bytes) -> tuple[str, str, list[dict]]:
    """(text, encoding name, warnings). Text uses "\\n" line ends and has no BOM."""
    warnings: list[dict] = []
    if not raw.strip():
        raise SubtitleError("SUBTITLE_EMPTY", "The subtitle file is empty.")
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        try:
            text, encoding = raw.decode("utf-16"), "utf-16"
        except UnicodeDecodeError:
            raise SubtitleError("SUBTITLE_ENCODING", "The subtitle file could not be read (UTF-16 expected).") from None
    else:
        if b"\x00" in raw:
            raise SubtitleError("SUBTITLE_BINARY", "This is not a text file: the subtitle must be a WebVTT or SubRip text file.")
        try:
            text, encoding = raw.decode("utf-8-sig"), "utf-8"
        except UnicodeDecodeError:
            try:
                text, encoding = raw.decode("cp1252"), "windows-1252"
            except UnicodeDecodeError:
                raise SubtitleError("SUBTITLE_ENCODING", "The subtitle file could not be read (use UTF-8).") from None
            _warn(warnings, "ENCODING_CONVERTED", "The file was not UTF-8; it was read as Windows-1252 and saved as UTF-8. Check umlauts.")
    return text.replace("\r\n", "\n").replace("\r", "\n").lstrip("﻿"), encoding, warnings


# ---------------- parsing ----------------


def _ms(h: str | None, m: str, s: str, frac: str) -> int:
    return ((int(h or 0) * 60 + int(m)) * 60 + int(s)) * 1000 + int(frac.ljust(3, "0")[:3])


def clean_text(text: str) -> str:
    """Plain, single-purpose text of one cue (see module docstring)."""
    text = _TAG.sub("", _BR.sub("\n", text))
    text = _CONTROL.sub("", html.unescape(text))
    lines = [_SPACES.sub(" ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def parse(text: str, warnings: list[dict] | None = None) -> tuple[list[Cue], str, list[dict]]:
    """Cues (sorted), format ("vtt"/"srt") and warnings of a decoded subtitle text."""
    warnings = warnings if warnings is not None else []
    lines = text.split("\n")
    first = next((ln.strip() for ln in lines if ln.strip()), "")
    fmt = "vtt" if first.startswith("WEBVTT") else "srt"
    arrows = [i for i, ln in enumerate(lines) if _ARROW.match(ln)]
    if not arrows:
        raise SubtitleError("SUBTITLE_FORMAT", "No cue with a valid time range (00:00:01.000 --> 00:00:03.000) was found. "
                                               "The file must be WebVTT (.vtt) or SubRip (.srt).")
    # a "-->" line that is not a valid time range is a broken cue
    broken = sum(1 for i, ln in enumerate(lines) if _ARROW_LOOSE.search(ln) and i not in set(arrows) and not ln.lstrip().startswith(("NOTE", "STYLE")))
    if broken:
        _warn(warnings, "BAD_TIMESTAMP", "Time range lines that could not be read were skipped.", broken)
    cues: list[Cue] = []
    bad_range = empty = cut = 0
    for n, at in enumerate(arrows):
        m = _ARROW.match(lines[at])
        start = _ms(*m.group(1, 2, 3, 4))
        end = _ms(*m.group(5, 6, 7, 8))
        stop = arrows[n + 1] if n + 1 < len(arrows) else len(lines)
        body = lines[at + 1:stop]
        # the identifier of the NEXT cue is the non-blank line directly above its time line: a number (SRT), or a label that
        # follows a blank line (WebVTT). A text line followed by a blank line is never touched.
        if n + 1 < len(arrows) and body and body[-1].strip():
            if re.fullmatch(r"\d+", body[-1].strip()) or (len(body) >= 2 and not body[-2].strip()):
                body.pop()
        # a cue ends at the first blank line (SRT and WebVTT text may not contain blank lines)
        text_lines: list[str] = []
        for ln in body:
            if not ln.strip():
                break
            text_lines.append(ln)
        if end <= start or start >= MAX_DAY_MS or end > MAX_DAY_MS:
            bad_range += 1
            continue
        clean = clean_text("\n".join(text_lines))
        if not clean:
            empty += 1
            continue
        if len(clean) > MAX_CUE_TEXT:
            clean, cut = clean[:MAX_CUE_TEXT].rstrip(), cut + 1
        cues.append(Cue(start, end, clean))
    if bad_range:
        _warn(warnings, "BAD_RANGE", "Cues whose end is not after their start (or beyond 24 h) were skipped.", bad_range)
    if empty:
        _warn(warnings, "EMPTY_CUE", "Cues without text were skipped.", empty)
    if cut:
        _warn(warnings, "TEXT_CUT", f"Cue texts longer than {MAX_CUE_TEXT} characters were cut.", cut)
    if not cues:
        raise SubtitleError("SUBTITLE_NO_CUES", "The file contains no usable cue (all had broken times or no text).")
    if len(cues) > MAX_CUES:
        raise SubtitleError("SUBTITLE_TOO_LARGE", f"More than {MAX_CUES} cues: this is not a film subtitle.")
    if any(cues[i].start > cues[i + 1].start for i in range(len(cues) - 1)):
        cues.sort(key=lambda c: (c.start, c.end))
        _warn(warnings, "UNSORTED", "The cues were not in time order; they were sorted.")
    return cues, fmt, warnings


def check(cues: list[Cue], video_ms: int | None, warnings: list[dict]) -> None:
    """Quality warnings (never errors): overlaps, extreme durations, long lines, and the fit to the video length."""
    overlaps = sum(1 for a, b in zip(cues, cues[1:]) if b.start < a.end)
    if overlaps:
        _warn(warnings, "OVERLAP", "Cues that overlap the previous one (both lines are shown together).", overlaps)
    short = sum(1 for c in cues if c.end - c.start < 150)
    if short:
        _warn(warnings, "VERY_SHORT", "Cues shorter than 0.15 s (hardly readable).", short)
    long_cues = sum(1 for c in cues if c.end - c.start > 15_000)
    if long_cues:
        _warn(warnings, "VERY_LONG", "Cues longer than 15 s.", long_cues)
    long_lines = sum(1 for c in cues for ln in c.text.split("\n") if len(ln) > MAX_LINE)
    if long_lines:
        _warn(warnings, "LONG_LINE", f"Lines longer than {MAX_LINE} characters.", long_lines)
    last = max(c.end for c in cues)
    if video_ms and video_ms > 0:
        # the stored length is rounded to whole minutes for older films: allow a minute plus 5 %
        if last > video_ms * 1.05 + 60_000:
            _warn(warnings, "BEYOND_VIDEO", f"The last cue ends at {_fmt_clock(last)} but the video is only {_fmt_clock(video_ms)} long "
                                            "(wrong file or wrong time base?).")
        elif video_ms > 600_000 and last < video_ms * 0.25:
            _warn(warnings, "ENDS_EARLY", f"The subtitle ends at {_fmt_clock(last)}, the video runs {_fmt_clock(video_ms)}: it covers only a small part.")


def _fmt_clock(ms: int) -> str:
    s = ms // 1000
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def analyze(raw: bytes, video_ms: int | None = None) -> Analysis:
    """Decode + parse + check one uploaded file. Raises `SubtitleError` when nothing usable is in it."""
    text, encoding, warnings = decode(raw)
    cues, fmt, warnings = parse(text, warnings)
    check(cues, video_ms, warnings)
    return Analysis(cues, fmt, encoding, warnings)


# ---------------- output ----------------


def _ts(ms: int) -> str:
    return f"{ms // 3_600_000:02d}:{ms // 60_000 % 60:02d}:{ms // 1000 % 60:02d}.{ms % 1000:03d}"


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def to_vtt(cues: list[Cue]) -> bytes:
    """The normalised WebVTT that is stored: header, one block per cue, escaped plain text, no identifiers or styles."""
    out = ["WEBVTT", ""]
    for c in cues:
        out += [f"{_ts(c.start)} --> {_ts(c.end)}", _esc(c.text), ""]
    return "\n".join(out).encode("utf-8")


def read_cues(raw: bytes) -> list[Cue]:
    """Cues of a stored file (also an older, not normalised one): always passed through the same sanitising parser."""
    text, _, warnings = decode(raw)
    return parse(text, warnings)[0]


def cues_json(cues: list[Cue]) -> list[list]:
    """Compact form for the player: [[start_ms, end_ms, text], …]."""
    return [[c.start, c.end, c.text] for c in cues]
