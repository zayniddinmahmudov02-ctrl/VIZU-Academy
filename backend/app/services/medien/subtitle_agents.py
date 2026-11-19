"""The subtitle agents: specialised steps that turn one piece of a film's audio into checked German subtitle lines.

    Hörer (listener)   — speech → timed German segments (subtitle_ai provider; Gemini answers in a fixed JSON schema, the fast model first)
    Prüfer (checker)   — rejects an answer that cannot be right: impossibly dense text, a phrase looping, no usable timing (an empty answer
                         gets a second listen from the fast model, then it is believed: credits / music / quiet scenes).
                         It then asks the listener again with the strong model; if that fails too, the piece is cut in two at
                         the pause nearest its middle and each half goes through the same agents. What still fails becomes a GAP (reported with
                         its time range, filled by "retry") — one bad piece never stops a film any more.
    Korrektor (proofreader) — a text-only pass per piece: German spelling, capitals, umlauts, punctuation; same number of lines, same times
                         (an answer with another count is ignored). Never blocks: on any error the lines stay as heard.
    Taktgeber (timing) and Übersetzer (translator) are the deterministic `build_cues` / `snap_to_speech` and the translation jobs (subtitle_jobs).

A service problem of the normal (fast) path is NOT turned into gaps or sent to the slow strong model: it is raised. The job waits and asks again when
the service is only busy (5xx / 429 / network, `subtitle_jobs._patiently`); a used-up quota or a rejected key stops the job and "retry" continues
later with the next piece. Nothing here touches the database (unit-tested in tests/test_medien_subtitle_agents.py)."""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass, field

from app.services.medien import subtitle_ai as ai

log = logging.getLogger("vizu.medien.subtitle_agents")

MAX_CHARS_PER_SECOND = 28  # faster than anybody speaks: an invented text
MIN_SPLIT_SECONDS = 40  # a piece shorter than this is not split again
MAX_DEPTH = 2  # 180 s → 90 s → 45 s
# errors that are about the service, not about this piece: stop the job instead of leaving a gap
SERVICE_ERRORS = ("AI_QUOTA", "AI_NETWORK", "AI_KEY_REJECTED", "AI_NOT_CONFIGURED")


def check_segments(segments: list[dict], seconds: float) -> list[str]:
    """The checker's rules for one piece (an empty list = accepted). Pure: unit-tested."""
    if not segments:
        return []  # silence / music: fine (the caller asks the strong model once before it believes it)
    problems = []
    chars = sum(len(s["text"]) for s in segments)
    if seconds > 0 and chars / seconds > MAX_CHARS_PER_SECOND:
        problems.append("TOO_DENSE")
    texts = [re.sub(r"\W+", " ", s["text"].lower()).strip() for s in segments]
    repeats = max(Counter(texts).values())
    run, longest = 1, 1
    for a, b in zip(texts, texts[1:]):
        run = run + 1 if a == b and a else 1
        longest = max(longest, run)
    if longest >= 4 or (len(texts) >= 8 and repeats / len(texts) > 0.5):
        problems.append("LOOP")
    for s in segments:
        words = s["text"].split()
        if len(words) >= 12 and len(set(w.lower() for w in words)) <= 2:
            problems.append("LOOP")
            break
    starts = [s["start"] for s in segments]
    if len(segments) >= 3 and (len(set(starts)) == 1 or sum(1 for s in segments if s["end"] - s["start"] > 15) > len(segments) / 2):
        problems.append("NO_TIMING")
    return sorted(set(problems))


def split_point(start: float, end: float, silences: list[tuple[float, float]], window: float = 15.0) -> float:
    """Where a piece is cut in two: the middle of the pause nearest its middle (±window), else the middle itself."""
    middle = (start + end) / 2
    near = [((s + e) / 2, e - s) for s, e in silences if abs((s + e) / 2 - middle) <= window and start + 5 < (s + e) / 2 < end - 5]
    if not near:
        return round(middle, 3)
    return round(min(near, key=lambda x: (abs(x[0] - middle), -x[1]))[0], 3)


@dataclass
class PieceResult:
    segments: list[dict] = field(default_factory=list)  # on the FILM clock
    language: str | None = None
    model: str | None = None
    steps: list[str] = field(default_factory=list)  # what the agents did, e.g. ["fast:LOOP", "strong:ok", "split", "proofread:3"]
    gaps: list[dict] = field(default_factory=list)  # [{"start": s, "end": e, "reason": "..."}]
    corrected: int = 0


def listen_and_check(provider, cut, start: float, end: float, language: str | None, silences: list[tuple[float, float]], depth: int = 0) -> PieceResult:
    """Hörer + Prüfer for [start, end) of the film. `cut(start, length)` → (bytes, mime). Raises only for a service problem (SERVICE_ERRORS)."""
    seconds = end - start
    result = PieceResult()
    data, mime = cut(start, seconds)

    def accept(heard, tag: str) -> PieceResult:
        result.steps.append(f"{tag}:ok")
        result.segments = [{**s, "start": round(s["start"] + start, 3), "end": round(s["end"] + start, 3)} for s in heard.segments]
        result.language, result.model = heard.language, heard.model
        return result

    def fast_again():
        try:
            return provider.transcribe(data, mime, language, seconds, strong=False)
        except ai.SubtitleAIError as exc:
            if exc.code in SERVICE_ERRORS or ai.is_transient(exc):
                raise
            return None

    for strong in (False, True):
        tag = "strong" if strong else "fast"
        try:
            heard = provider.transcribe(data, mime, language, seconds, strong=strong)
        except ai.SubtitleAIError as exc:
            if not strong and (exc.code in SERVICE_ERRORS or ai.is_transient(exc)):
                raise  # the normal path itself is unavailable or busy: the job waits / stops (never minutes on the slow model for nothing)
            result.steps.append(f"{tag}:{exc.code}")  # the strong model unavailable / a bad answer: go on with the next step
            continue
        problems = check_segments(heard.segments, seconds)
        if not problems and heard.segments:
            return accept(heard, tag)
        if not problems:  # nothing heard (credits, music, a quiet scene)
            if strong:
                return accept(heard, tag)
            # a second listen with the FAST model before silence is believed: the slow strong model is not worth minutes here (seen live:
            # every quiet piece at the end of a film took 5–10 min on it)
            result.steps.append("fast:EMPTY")
            again = fast_again()
            if again is not None and again.segments and not check_segments(again.segments, seconds):
                return accept(again, "fast2")
            result.steps.append("quiet")
            result.language, result.model = heard.language, heard.model
            return result
        result.steps.append(f"{tag}:{','.join(problems)}")
    # both answers unusable: cut the piece in two and try each half (smaller answers are more reliable)
    if seconds >= MIN_SPLIT_SECONDS and depth < MAX_DEPTH:
        middle = split_point(start, end, silences)
        result.steps.append("split")
        for a, b in ((start, middle), (middle, end)):
            half = listen_and_check(provider, cut, a, b, language, silences, depth + 1)
            result.segments += half.segments
            result.gaps += half.gaps
            result.steps += [f"half:{s}" for s in half.steps]
            result.language = result.language or half.language
            result.model = result.model or half.model
        return result
    reason = result.steps[-1].split(":", 1)[-1] if result.steps else "UNKNOWN"
    result.gaps.append({"start": round(start, 3), "end": round(end, 3), "reason": reason})
    log.warning("subtitle piece %.0f-%.0f s left as a gap (%s)", start, end, reason)
    return result


def proofread(result: PieceResult, proof) -> PieceResult:
    """Korrektor: corrects the lines of one piece in place (same count / times). Any failure keeps the lines as heard."""
    if proof is None or not result.segments:
        return result
    lines = [s["text"] for s in result.segments]
    try:
        fixed = proof.proofread(lines)
    except ai.SubtitleAIError as exc:
        if exc.code in ("AI_QUOTA",):
            result.steps.append("proofread:skipped-quota")
        else:
            result.steps.append(f"proofread:{exc.code}")
        return result
    except Exception:  # never lose a heard piece because of the proofreading
        log.exception("proofreading failed")
        result.steps.append("proofread:error")
        return result
    if len(fixed) != len(lines):
        result.steps.append("proofread:count")
        return result
    changed = 0
    for s, new in zip(result.segments, fixed):
        if new and new != s["text"]:
            s["text"], changed = new, changed + 1
    result.corrected = changed
    result.steps.append(f"proofread:{changed}")
    return result
