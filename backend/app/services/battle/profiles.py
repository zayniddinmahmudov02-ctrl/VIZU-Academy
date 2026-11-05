"""Battle profiles: created on first use, the caller is always the token's user. Public player data is
the display name (first name, else username), the uploaded profile photo (`users.profile_image`, else the
chosen game avatar), rank and Battle Points — never e-mail or phone."""

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.battle import BattleMatch, BattleProfile
from app.models.user import User
from app.services.battle import config

LEADERBOARD_PAGE = 20


def get_profile(db: Session, user_id, lock: bool = False) -> BattleProfile:
    db.execute(pg_insert(BattleProfile).values(user_id=user_id).on_conflict_do_nothing(index_elements=["user_id"]))
    q = select(BattleProfile).where(BattleProfile.user_id == user_id)
    if lock:
        q = q.with_for_update()
    return db.execute(q).scalar_one()


def display_name(user: User | None) -> str:
    if user is None:
        return config.BOT_NAME
    return (user.first_name or "").strip() or user.username


def player_card(user: User | None, profile: BattleProfile | None) -> dict:
    points = profile.points if profile else 0
    rank = config.rank_info(points)
    return {
        "name": display_name(user), "avatar": profile.avatar if profile else "bot", "photo": user.profile_image if user else None, "points": points,
        "rank": rank["title"], "stage": rank["stage"], "is_bot": user is None,
    }


def stats(profile: BattleProfile) -> dict:
    played = profile.wins + profile.losses + profile.draws
    return {
        "matches": played, "wins": profile.wins, "losses": profile.losses, "draws": profile.draws,
        "win_rate": round(profile.wins / played, 3) if played else 0.0, "streak": profile.streak, "best_streak": profile.best_streak,
    }


def achievements(profile: BattleProfile) -> list[dict]:
    s = stats(profile)
    values = {"matches": s["matches"], "wins": profile.wins, "best_streak": profile.best_streak, "rank": config.rank_index(profile.points)}
    return [
        {"key": key, "title_de": de, "title_uz": uz, "unlocked": values[kind] >= threshold, "progress": min(values[kind], threshold), "goal": threshold}
        for key, de, uz, kind, threshold in config.ACHIEVEMENTS
    ]


def avatars(profile: BattleProfile) -> list[dict]:
    i = config.rank_index(profile.points)
    return [
        {"key": key, "title": title, "unlocked": i >= need, "unlock_rank": config.rank_title(need), "selected": profile.avatar == key}
        for key, (title, need) in config.AVATARS.items()
    ]


def set_avatar(db: Session, user: User, key: str) -> dict:
    if key not in config.AVATARS:
        raise HTTPException(422, "AVATAR_UNKNOWN")
    profile = get_profile(db, user.id, lock=True)
    if config.rank_index(profile.points) < config.AVATARS[key][1]:
        raise HTTPException(403, "AVATAR_LOCKED")
    profile.avatar = key
    db.commit()
    return {"avatar": key, "avatars": avatars(profile)}


def leaderboard(db: Session, user: User, stage: str | None = None, page: int = 1, size: int = LEADERBOARD_PAGE) -> dict:
    q = select(BattleProfile, User).join(User, User.id == BattleProfile.user_id).where(
        User.is_active.is_(True), User.is_banned.is_(False), or_(BattleProfile.wins + BattleProfile.losses + BattleProfile.draws > 0, BattleProfile.user_id == user.id)
    )
    if stage:
        if stage not in config.STAGES:
            raise HTTPException(422, "STAGE_UNKNOWN")
        i = config.STAGES.index(stage)
        lo, hi = i * 3 * config.RANK_STEP, (i + 1) * 3 * config.RANK_STEP
        q = q.where(BattleProfile.points >= lo)
        if stage != "C1+":
            q = q.where(BattleProfile.points < hi)
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    rows = db.execute(
        q.order_by(BattleProfile.points.desc(), BattleProfile.wins.desc(), BattleProfile.created_at).offset((page - 1) * size).limit(size)
    ).all()
    items = [
        {"position": (page - 1) * size + n + 1, **player_card(u, p), "wins": p.wins, "matches": p.wins + p.losses + p.draws, "me": u.id == user.id}
        for n, (p, u) in enumerate(rows)
    ]
    me = get_profile(db, user.id)
    my_pos = db.execute(
        select(func.count()).select_from(BattleProfile).join(User, User.id == BattleProfile.user_id)
        .where(User.is_active.is_(True), User.is_banned.is_(False), BattleProfile.points > me.points)
    ).scalar_one() + 1
    return {"items": items, "total": total, "page": page, "page_size": size, "me": {"position": my_pos, **player_card(user, me)}}


def recent_matches(db: Session, user: User, limit: int = 8) -> list[dict]:
    rows = db.execute(
        select(BattleMatch).where(or_(BattleMatch.player1_id == user.id, BattleMatch.player2_id == user.id), BattleMatch.status == "finished")
        .order_by(BattleMatch.finished_at.desc()).limit(limit)
    ).scalars().all()
    other_ids = {m.player2_id if m.player1_id == user.id else m.player1_id for m in rows} - {None}
    users = {u.id: u for u in db.execute(select(User).where(User.id.in_(other_ids))).scalars()} if other_ids else {}
    out = []
    for m in rows:
        slot = 1 if m.player1_id == user.id else 2
        opp_id = m.player2_id if slot == 1 else m.player1_id
        result = "draw" if m.winner_slot == 0 else ("win" if m.winner_slot == slot else "loss")
        out.append({
            "id": str(m.id), "mode": m.mode, "stage": m.level, "result": result, "finish_reason": m.finish_reason,
            "my_score": m.p1_score if slot == 1 else m.p2_score, "opponent_score": m.p2_score if slot == 1 else m.p1_score,
            "points_delta": m.p1_delta if slot == 1 else m.p2_delta, "opponent": display_name(users.get(opp_id)) if opp_id else config.BOT_NAME,
            "opponent_photo": users[opp_id].profile_image if opp_id in users else None,
            "finished_at": m.finished_at.isoformat() if m.finished_at else None,
        })
    return out
