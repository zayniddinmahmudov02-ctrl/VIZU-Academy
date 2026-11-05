"""Seed of the Battle content shipped in app/data/battle: picture words (words.json), their checked
pictures (images.json + images/*.webp) and the six arena themes (themes.json).

Plan (read-only) → apply --confirm <plan id>. Idempotent: words are keyed by the Wörterbuch row,
pictures by sha256, themes by stage; existing rows keep what admins changed (status, category, theme).
Stops when a Wörterbuch row is missing, not VERIFIED/published or has another article / lemma than
words.json, or when a picture file's sha256 differs from the manifest."""

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.models.battle import BattleImage, BattleTheme, BattleWord
from app.models.dictionary import DictionaryEntry
from app.services.battle import media, questions, themes

DATA = Path(__file__).resolve().parents[2] / "data" / "battle"
MANIFEST = DATA / "images.json"


class SeedError(Exception):
    pass


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["images"] if MANIFEST.exists() else {}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_plan(db: Session) -> dict:
    data = questions.word_data()
    manifest = _manifest()
    problems, words, images = [], [], []
    for w in data["words"]:
        e = db.execute(select(DictionaryEntry).where(DictionaryEntry.level == w["level"], DictionaryEntry.source_id == w["source_id"])).scalar_one_or_none()
        key = f"{w['level']}-{w['source_id']}"
        if e is None:
            problems.append(f"{key}: Wörterbuch row missing")
            continue
        if e.status != "verified" or not e.is_published or (e.article or None) != (w["article"] or None) or e.lemma != w["lemma"]:
            problems.append(f"{key}: Wörterbuch row is {e.status}/{e.article} {e.lemma}, words.json says {w['article']} {w['lemma']}")
            continue
        if w["category"] not in data["categories"]:
            problems.append(f"{key}: unknown category {w['category']}")
            continue
        existing = db.execute(select(BattleWord).where(BattleWord.entry_id == e.id)).scalar_one_or_none()
        pic = manifest.get(w["lemma"])
        img_action = None
        if pic:
            path = DATA / pic["file"]
            if not path.is_file() or _sha(path) != pic["sha256"]:
                problems.append(f"{key}: picture {pic['file']} missing or sha256 differs")
                continue
            found = db.execute(select(BattleImage.id).where(BattleImage.sha256 == pic["sha256"])).first()
            img_action = "keep" if found else "create"
            if img_action == "create":
                images.append(w["lemma"])
        words.append({"key": key, "word": f"{w['article']} {w['lemma']}", "category": w["category"],
                      "action": "keep" if existing else "create", "image": img_action or "none"})
    existing_themes = {t.level for t in db.execute(select(BattleTheme)).scalars()}
    theme_rows = [{"stage": t["stage"], "action": "keep" if t["stage"] in existing_themes else "create"} for t in themes.defaults()]
    plan = {"words": words, "images_to_create": images, "themes": theme_rows, "problems": problems,
            "counts": {"words_create": sum(w["action"] == "create" for w in words), "images_create": len(images),
                       "themes_create": sum(t["action"] == "create" for t in theme_rows)}}
    plan["plan_id"] = hashlib.sha256(json.dumps({k: plan[k] for k in ("words", "images_to_create", "themes", "problems")}, sort_keys=True).encode()).hexdigest()[:12]
    return plan


def apply(db: Session, confirm: str) -> dict:
    plan = build_plan(db)
    if plan["plan_id"] != confirm:
        raise SeedError(f"plan id changed: expected {confirm}, current {plan['plan_id']} — run plan again")
    if plan["problems"]:
        raise SeedError("plan has problems: " + "; ".join(plan["problems"][:5]))
    now = datetime.now(timezone.utc)
    data = questions.word_data()
    manifest = _manifest()
    created_words = created_images = 0
    copied: list[Path] = []
    try:
        for w in data["words"]:
            e = db.execute(select(DictionaryEntry).where(DictionaryEntry.level == w["level"], DictionaryEntry.source_id == w["source_id"])).scalar_one()
            word = db.execute(select(BattleWord).where(BattleWord.entry_id == e.id)).scalar_one_or_none()
            if word is None:
                word = BattleWord(entry_id=e.id, level=e.level, article=e.article, lemma=e.lemma, translation=e.translation, category=w["category"], status="draft")
                db.add(word)
                db.flush()
                created_words += 1
            pic = manifest.get(w["lemma"])
            if not pic:
                continue
            img = db.execute(select(BattleImage).where(BattleImage.sha256 == pic["sha256"])).scalar_one_or_none()
            if img is None:
                media.IMAGE_ROOT.mkdir(parents=True, exist_ok=True)
                name = f"{hashlib.sha256((pic['sha256'] + str(now)).encode()).hexdigest()[:32]}.webp"
                shutil.copyfile(DATA / pic["file"], media.IMAGE_ROOT / name)
                copied.append(media.IMAGE_ROOT / name)
                img = BattleImage(storage_name=name, mime="image/webp", width=pic["width"], height=pic["height"], size_bytes=pic["size_bytes"],
                                  sha256=pic["sha256"], source="wikimedia", source_url=pic["page_url"], file_title=pic["title"], author=pic["author"],
                                  license=pic["license"], license_url=pic.get("license_url"), status="published", review_note=pic.get("review_note"),
                                  verified_at=now)
                db.add(img)
                db.flush()
                created_images += 1
            if word.image_id is None:
                word.image_id = img.id
                if word.status == "draft" and img.status == "published":
                    word.status = "published"
        existing = {t.level for t in db.execute(select(BattleTheme)).scalars()}
        created_themes = 0
        for t in themes.defaults():
            if t["stage"] in existing:
                continue
            db.add(BattleTheme(level=t["stage"], **{f: t[f] for f in themes.FIELDS}, published_at=now))
            created_themes += 1
        write_audit(db, None, "battle_seed_apply", details=json.dumps({"plan_id": confirm, "words": created_words, "images": created_images, "themes": created_themes}))
        db.commit()
    except Exception:
        db.rollback()
        for p in copied:
            p.unlink(missing_ok=True)
        raise
    return {"plan_id": confirm, "words_created": created_words, "images_created": created_images, "themes_created": created_themes}
