"""Game Management → Battle: picture words, image library, overview.

Rules: a word comes only from a VERIFIED, published Wörterbuch row; a word is `published` only with a
`published` image; an image is published only with author + licence (Wikimedia imports carry them, an
upload needs them typed in). Rejecting a picture takes its words back to draft. Every write is audited."""

import json
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.models.battle import BattleImage, BattleMatch, BattleProfile, BattleWord
from app.models.dictionary import DictionaryEntry
from app.models.user import User
from app.services.battle import commons, config, media, questions

WORD_STATUSES = ("draft", "published", "disabled")
IMAGE_STATUSES = ("draft", "verified", "published", "rejected")
PAGE = 30


def _now():
    return datetime.now(timezone.utc)


def image_view(img: BattleImage | None) -> dict | None:
    if img is None:
        return None
    return {
        "id": str(img.id), "status": img.status, "source": img.source, "source_url": img.source_url, "file_title": img.file_title,
        "author": img.author, "license": img.license, "license_url": img.license_url, "width": img.width, "height": img.height,
        "size_bytes": img.size_bytes, "review_note": img.review_note, "verified_at": img.verified_at.isoformat() if img.verified_at else None,
    }


def word_view(w: BattleWord, img: BattleImage | None) -> dict:
    return {
        "id": str(w.id), "level": w.level, "article": w.article, "lemma": w.lemma, "display": w.display, "translation": w.translation,
        "category": w.category, "status": w.status, "image": image_view(img),
    }


def overview(db: Session) -> dict:
    words = db.execute(
        select(BattleWord.level, BattleWord.status, BattleImage.status, func.count())
        .outerjoin(BattleImage, BattleImage.id == BattleWord.image_id).group_by(BattleWord.level, BattleWord.status, BattleImage.status)
    ).all()
    levels = {lv: {"words": 0, "published": 0, "playable": 0, "without_image": 0} for lv in config.WORD_LEVELS}
    for lv, ws, ims, n in words:
        row = levels.setdefault(lv, {"words": 0, "published": 0, "playable": 0, "without_image": 0})
        row["words"] += n
        row["published"] += n if ws == "published" else 0
        row["playable"] += n if ws == "published" and ims == "published" else 0
        row["without_image"] += n if ims is None else 0
    images = dict(db.execute(select(BattleImage.status, func.count()).group_by(BattleImage.status)).all())
    week = _now() - timedelta(days=7)
    matches = db.execute(select(BattleMatch.mode, BattleMatch.status, func.count()).where(BattleMatch.created_at >= week)
                         .group_by(BattleMatch.mode, BattleMatch.status)).all()
    return {
        "levels": levels, "images": {s: images.get(s, 0) for s in IMAGE_STATUSES},
        "stages": {s: {"pool": questions.pool_size(db, s), "ready": questions.pool_size(db, s) >= config.MIN_POOL} for s in config.STAGES},
        "matches_7d": [{"mode": m, "status": s, "count": n} for m, s, n in matches],
        "players": db.execute(select(func.count()).select_from(BattleProfile).where(BattleProfile.wins + BattleProfile.losses + BattleProfile.draws > 0)).scalar_one(),
        "categories": questions.categories(), "min_pool": config.MIN_POOL,
    }


def list_words(db: Session, level: str | None, status: str | None, category: str | None, q: str, page: int) -> dict:
    query = select(BattleWord, BattleImage).outerjoin(BattleImage, BattleImage.id == BattleWord.image_id)
    if level:
        query = query.where(BattleWord.level == level)
    if status:
        query = query.where(BattleWord.status == status)
    if category:
        query = query.where(BattleWord.category == category)
    if q.strip():
        like = f"%{q.strip().lower()}%"
        query = query.where(or_(func.lower(BattleWord.lemma).like(like), func.lower(BattleWord.translation).like(like)))
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    rows = db.execute(query.order_by(BattleWord.level, BattleWord.category, BattleWord.lemma).offset((page - 1) * PAGE).limit(PAGE)).all()
    return {"items": [word_view(w, i) for w, i in rows], "total": total, "page": page, "page_size": PAGE}


def _word(db: Session, word_id) -> BattleWord:
    w = db.execute(select(BattleWord).where(BattleWord.id == word_id).with_for_update()).scalar_one_or_none()
    if w is None:
        raise HTTPException(404, "WORD_NOT_FOUND")
    return w


def _image(db: Session, image_id) -> BattleImage:
    img = db.execute(select(BattleImage).where(BattleImage.id == image_id).with_for_update()).scalar_one_or_none()
    if img is None:
        raise HTTPException(404, "IMAGE_NOT_FOUND")
    return img


def add_word(db: Session, actor: User, dictionary_id: str, category: str) -> dict:
    if category not in questions.categories():
        raise HTTPException(422, "CATEGORY_UNKNOWN")
    try:
        level, source_id = dictionary_id.split("-", 1)
        source_id = int(source_id)
    except ValueError:
        raise HTTPException(422, "DICTIONARY_ID_INVALID")
    e = db.execute(select(DictionaryEntry).where(DictionaryEntry.level == level, DictionaryEntry.source_id == source_id)).scalar_one_or_none()
    if e is None:
        raise HTTPException(404, "DICTIONARY_ENTRY_NOT_FOUND")
    if e.status != "verified" or not e.is_published:
        raise HTTPException(422, "DICTIONARY_ENTRY_NOT_VERIFIED")
    if db.execute(select(BattleWord.id).where(BattleWord.entry_id == e.id)).first():
        raise HTTPException(409, "WORD_EXISTS")
    w = BattleWord(entry_id=e.id, level=e.level, article=e.article, lemma=e.lemma, translation=e.translation, category=category, status="draft")
    db.add(w)
    db.flush()
    write_audit(db, str(actor.id), "battle_word_add", details=json.dumps({"word": str(w.id), "dictionary": dictionary_id}))
    db.commit()
    return word_view(w, None)


def update_word(db: Session, actor: User, word_id, data: dict) -> dict:
    w = _word(db, word_id)
    if "category" in data:
        if data["category"] not in questions.categories():
            raise HTTPException(422, "CATEGORY_UNKNOWN")
        w.category = data["category"]
    if "status" in data:
        if data["status"] not in WORD_STATUSES:
            raise HTTPException(422, "STATUS_UNKNOWN")
        if data["status"] == "published":
            img = db.get(BattleImage, w.image_id) if w.image_id else None
            if img is None or img.status != "published":
                raise HTTPException(409, "WORD_NEEDS_PUBLISHED_IMAGE")
        w.status = data["status"]
    write_audit(db, str(actor.id), "battle_word_update", details=json.dumps({"word": str(w.id), **data}))
    db.commit()
    return word_view(w, db.get(BattleImage, w.image_id) if w.image_id else None)


def _attach(db: Session, actor: User, w: BattleWord, webp: bytes, width: int, height: int, meta: dict) -> BattleImage:
    img = BattleImage(storage_name=media.store(media.IMAGE_ROOT, webp), mime="image/webp", width=width, height=height, size_bytes=len(webp),
                      sha256=media.sha256(webp), status="draft", created_by=actor.id, **meta)
    db.add(img)
    db.flush()
    w.image_id = img.id
    if w.status == "published":
        w.status = "draft"
    return img


def upload_image(db: Session, actor: User, word_id, data: bytes, filename: str | None, content_type: str | None,
                 author: str, license: str, source_url: str | None) -> dict:
    w = _word(db, word_id)
    webp, width, height = media.normalise(data, filename, content_type, media.WORD_MAX_SIDE)
    img = _attach(db, actor, w, webp, width, height, {"source": "upload", "author": author.strip()[:300] or None,
                                                     "license": license.strip()[:80] or None, "source_url": (source_url or "").strip()[:500] or None})
    write_audit(db, str(actor.id), "battle_image_upload", details=json.dumps({"word": str(w.id), "image": str(img.id)}))
    db.commit()
    return word_view(w, img)


def commons_import(db: Session, actor: User, word_id, title: str) -> dict:
    w = _word(db, word_id)
    item, raw = commons.fetch(title)
    webp, width, height = media.normalise(raw, None, None, media.WORD_MAX_SIDE)
    img = _attach(db, actor, w, webp, width, height, {
        "source": "wikimedia", "file_title": item["title"][:300], "source_url": item["page_url"], "author": item["author"],
        "license": item["license"][:80], "license_url": item["license_url"],
    })
    write_audit(db, str(actor.id), "battle_image_commons", details=json.dumps({"word": str(w.id), "image": str(img.id), "title": item["title"]}))
    db.commit()
    return word_view(w, img)


def set_image_status(db: Session, actor: User, image_id, status: str, note: str | None) -> dict:
    if status not in IMAGE_STATUSES:
        raise HTTPException(422, "STATUS_UNKNOWN")
    img = _image(db, image_id)
    if status == "published" and not (img.author and img.license):
        raise HTTPException(422, "IMAGE_ATTRIBUTION_REQUIRED: Autor und Lizenz sind Pflicht")
    if status == "published" and img.status not in ("verified", "published"):
        raise HTTPException(409, "IMAGE_NOT_VERIFIED: erst prüfen (Verified), dann veröffentlichen")
    img.status = status
    if note is not None:
        img.review_note = note.strip()[:1000] or None
    if status in ("verified", "published") and img.verified_at is None:
        img.verified_by, img.verified_at = actor.id, _now()
    if status in ("draft", "rejected"):
        for w in db.execute(select(BattleWord).where(BattleWord.image_id == img.id, BattleWord.status == "published")).scalars():
            w.status = "draft"
    write_audit(db, str(actor.id), "battle_image_status", details=json.dumps({"image": str(img.id), "status": status}))
    db.commit()
    return image_view(img)


def image_file(db: Session, image_id):
    img = db.get(BattleImage, image_id)
    if img is None:
        raise HTTPException(404, "IMAGE_NOT_FOUND")
    return media.serve(media.safe_path(media.IMAGE_ROOT, img.storage_name))
