"""Question types of Lesen / Hören tests (all levels A1-C1).

Option-based (answer key = `is_correct` on the options table):
* MULTIPLE_CHOICE — answer: option id
* TRUE_FALSE      — answer: option id ("Richtig" / "Falsch")

Config-based (answer key inside `question.config`, never sent to students):
* MATCHING (Zuordnung) — config {"items": [{"id","text"}], "targets": [{"id","text"}],
  "pairs": {item_id: target_id}}; answer {item_id: target_id}. Targets may
  include distractors. Partial credit per item.
* GAP_FILL (Lückentext) — config {"text": "Ich [[1]] Tom.", "gaps": {"1": {"accepted":
  ["heiße", "heisse"], "options": [...]?}}, "case_sensitive": false}; answer
  {gap_id: text}. With "options" the gap is a choice list. Partial credit per gap.
* SHORT_ANSWER — config {"accepted": ["Taschkent", "In Taschkent"],
  "case_sensitive": false, "max_length": 100}; answer: text. Only answers that a
  key can decide reliably — free answers are NOT auto-graded.

Text answers are compared after Unicode NFC normalisation, trimming, collapsing
whitespace and dropping trailing . ! ? (and case unless case_sensitive)."""

import hashlib
import re
import unicodedata

from app.models.lesson_skill import (
    QUESTION_GAP_FILL,
    QUESTION_MATCHING,
    QUESTION_SHORT_ANSWER,
    QUESTION_TRUE_FALSE,
    QUESTION_TYPES,
)

GAP_PATTERN = re.compile(r"\[\[([A-Za-z0-9_-]{1,20})\]\]")
MAX_TEXT_ANSWER = 300


class QuestionConfigError(ValueError):
    pass


# ============================================================
# Normalisation
# ============================================================


def normalise_text(value, case_sensitive: bool = False) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    text = " ".join(text.split()).strip()
    text = text.rstrip(".!?").strip()
    return text if case_sensitive else text.casefold()


def _clean_str(value, limit: int) -> str:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        raise QuestionConfigError("empty text")
    if len(text) > limit:
        raise QuestionConfigError(f"text longer than {limit} characters")
    return text


def _accepted(values, label: str) -> list[str]:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list) or not values:
        raise QuestionConfigError(f"{label}: at least one accepted answer is required")
    out = []
    for v in values[:20]:
        out.append(_clean_str(v, 200))
    return out


# ============================================================
# Validation of the admin / import definition
# ============================================================


def validate_config(qtype: str, config) -> dict | None:
    """Returns the cleaned config (with key) or raises QuestionConfigError."""
    if qtype not in QUESTION_TYPES:
        raise QuestionConfigError(f"unknown question type '{qtype}'")
    if qtype in (QUESTION_TRUE_FALSE, "MULTIPLE_CHOICE"):
        return None
    if not isinstance(config, dict):
        raise QuestionConfigError("config is required for this question type")

    if qtype == QUESTION_MATCHING:
        items, targets, pairs = config.get("items"), config.get("targets"), config.get("pairs")
        if not isinstance(items, list) or not 2 <= len(items) <= 12:
            raise QuestionConfigError("Zuordnung: 2-12 items are required")
        if not isinstance(targets, list) or not len(items) <= len(targets) <= 15:
            raise QuestionConfigError("Zuordnung: at least as many targets as items (max 15)")
        if not isinstance(pairs, dict):
            raise QuestionConfigError("Zuordnung: 'pairs' (item id -> target id) is required")
        clean_items, clean_targets = [], []
        for label, src, dst in (("item", items, clean_items), ("target", targets, clean_targets)):
            seen = set()
            for i, entry in enumerate(src, start=1):
                if not isinstance(entry, dict):
                    raise QuestionConfigError(f"Zuordnung: {label} {i} must be an object")
                eid = str(entry.get("id") or i).strip()[:20]
                if eid in seen:
                    raise QuestionConfigError(f"Zuordnung: duplicate {label} id '{eid}'")
                seen.add(eid)
                dst.append({"id": eid, "text": _clean_str(entry.get("text"), 300)})
        target_ids = {t["id"] for t in clean_targets}
        clean_pairs = {}
        for item in clean_items:
            target = str(pairs.get(item["id"], "")).strip()
            if target not in target_ids:
                raise QuestionConfigError(f"Zuordnung: item '{item['id']}' has no valid target in 'pairs'")
            clean_pairs[item["id"]] = target
        return {"items": clean_items, "targets": clean_targets, "pairs": clean_pairs}

    if qtype == QUESTION_GAP_FILL:
        text = str(config.get("text") or "").strip()
        if not text or len(text) > 5000:
            raise QuestionConfigError("Lückentext: 'text' with [[gap]] placeholders is required (max 5000)")
        gap_ids = GAP_PATTERN.findall(text)
        if not gap_ids:
            raise QuestionConfigError("Lückentext: the text contains no [[gap]] placeholder")
        if len(gap_ids) != len(set(gap_ids)) or len(gap_ids) > 20:
            raise QuestionConfigError("Lückentext: gap ids must be unique (max 20 gaps)")
        gaps = config.get("gaps")
        if not isinstance(gaps, dict):
            raise QuestionConfigError("Lückentext: 'gaps' is required")
        clean_gaps = {}
        for gid in gap_ids:
            gap = gaps.get(gid)
            if isinstance(gap, (list, str)):
                gap = {"accepted": gap}
            if not isinstance(gap, dict):
                raise QuestionConfigError(f"Lückentext: gap [[{gid}]] has no answer")
            accepted = _accepted(gap.get("accepted"), f"Lückentext gap [[{gid}]]")
            entry = {"accepted": accepted}
            if gap.get("options"):
                options = [_clean_str(o, 100) for o in gap["options"]][:8]
                if len(options) < 2:
                    raise QuestionConfigError(f"Lückentext: gap [[{gid}]] needs 2+ options")
                if not any(normalise_text(a) == normalise_text(o) for a in accepted for o in options):
                    raise QuestionConfigError(f"Lückentext: the answer of gap [[{gid}]] is not among its options")
                entry["options"] = options
            clean_gaps[gid] = entry
        extra = set(gaps) - set(gap_ids)
        if extra:
            raise QuestionConfigError(f"Lückentext: answers for unknown gaps {sorted(extra)}")
        return {"text": text, "gaps": clean_gaps, "case_sensitive": bool(config.get("case_sensitive"))}

    # SHORT_ANSWER
    max_length = config.get("max_length", 100)
    try:
        max_length = int(max_length)
    except (TypeError, ValueError):
        raise QuestionConfigError("Kurzantwort: max_length must be a number") from None
    if not 1 <= max_length <= MAX_TEXT_ANSWER:
        raise QuestionConfigError(f"Kurzantwort: max_length 1-{MAX_TEXT_ANSWER}")
    return {
        "accepted": _accepted(config.get("accepted"), "Kurzantwort"),
        "case_sensitive": bool(config.get("case_sensitive")),
        "max_length": max_length,
    }


# ============================================================
# Student view (no key)
# ============================================================


def _shuffled(entries: list[dict], seed: str) -> list[dict]:
    """Deterministic order that differs from the authoring order."""
    return sorted(entries, key=lambda e: hashlib.sha256(f"{seed}:{e['id']}".encode()).hexdigest())


def public_config(question) -> dict | None:
    config = question.config or {}
    qtype = question.question_type
    if qtype == QUESTION_MATCHING:
        return {
            "items": [{"id": i["id"], "text": i["text"]} for i in config.get("items", [])],
            "targets": [{"id": t["id"], "text": t["text"]} for t in _shuffled(config.get("targets", []), str(question.id))],
        }
    if qtype == QUESTION_GAP_FILL:
        gaps = config.get("gaps", {})
        return {
            "text": config.get("text", ""),
            "gaps": [
                {"id": gid, **({"options": _shuffled([{"id": o, "text": o} for o in g["options"]], f"{question.id}:{gid}")} if g.get("options") else {})}
                for gid, g in ((gid, gaps.get(gid, {})) for gid in GAP_PATTERN.findall(config.get("text", "")))
            ],
        }
    if qtype == QUESTION_SHORT_ANSWER:
        return {"max_length": config.get("max_length", 100)}
    return None


# ============================================================
# Grading (pure)
# ============================================================


def clean_answer(qtype: str, value):
    """Shape check of a submitted answer — anything else counts as unanswered."""
    if qtype in (QUESTION_MATCHING, QUESTION_GAP_FILL):
        if not isinstance(value, dict):
            return None
        out = {str(k)[:20]: str(v)[:MAX_TEXT_ANSWER] for k, v in list(value.items())[:30] if v not in (None, "")}
        return out or None
    if value is None or isinstance(value, (dict, list)):
        return None
    text = str(value)[:MAX_TEXT_ANSWER]
    return text if text.strip() else None


def grade_config_question(question, answer) -> dict:
    """Returns {fraction, selected, correct_answer, details} for a config-based question."""
    config = question.config or {}
    qtype = question.question_type
    if qtype == QUESTION_MATCHING:
        pairs = config.get("pairs", {})
        given = answer if isinstance(answer, dict) else {}
        details = {item_id: given.get(item_id) == target for item_id, target in pairs.items()}
        fraction = sum(details.values()) / len(pairs) if pairs else 0.0
        return {"fraction": fraction, "selected": given or None, "correct_answer": pairs, "details": details}
    if qtype == QUESTION_GAP_FILL:
        cs = bool(config.get("case_sensitive"))
        gaps = config.get("gaps", {})
        given = answer if isinstance(answer, dict) else {}
        details = {
            gid: normalise_text(given.get(gid), cs) in {normalise_text(a, cs) for a in g.get("accepted", [])} and bool(str(given.get(gid) or "").strip())
            for gid, g in gaps.items()
        }
        fraction = sum(details.values()) / len(gaps) if gaps else 0.0
        return {
            "fraction": fraction,
            "selected": given or None,
            "correct_answer": {gid: g.get("accepted", [""])[0] for gid, g in gaps.items()},
            "details": details,
        }
    # SHORT_ANSWER
    cs = bool(config.get("case_sensitive"))
    accepted = config.get("accepted", [])
    ok = isinstance(answer, str) and bool(answer.strip()) and normalise_text(answer, cs) in {normalise_text(a, cs) for a in accepted}
    return {"fraction": 1.0 if ok else 0.0, "selected": answer if isinstance(answer, str) else None,
            "correct_answer": accepted[0] if accepted else None, "details": None}
