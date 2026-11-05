"""Matchmaking and the match engine: server-authoritative, state in PostgreSQL, clients poll.

Why polling: production runs one uvicorn worker without a WebSocket library and nginx has no upgrade
headers for /api; PostgreSQL state works with any worker count. Every read of a match locks its row and
advances it to "now" (`tick`), so the clock is the server's and catching up after a gap is deterministic:
countdown → round 1 … ROUNDS (ROUND_S each, ends early when both answered) → REVEAL_S → … → finished.

* Ranked: same arena stage; the points window widens with the longer waiting time (config.MATCH_WINDOWS).
  Matchmaking per stage is serialised with a transaction advisory lock, and a waiting player re-runs it on
  every poll, so two waiting players always meet.
* Private: a 6-character room code, no Battle Points. Bot: practice against VIZU Bot, no Battle Points.
* Answers: one per player and round (unique constraint), time measured by the server from the round
  start, ANSWER_GRACE_MS of network slack. The correct option is sent only after the round has ended.
* A player who has not polled for AFK_S loses (reconnecting inside that window continues the match);
  leaving is a forfeit. Points go through battle_points_ledger (unique per user + match = idempotent)."""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import or_, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.battle import BattleAnswer, BattleMatch, BattlePointsLedger, BattleWord
from app.models.notification import TYPE_BATTLE, Notification
from app.models.user import User
from app.services.battle import config, media, profiles, questions

ROOM_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
OPEN = ("waiting", "active")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ms(delta: timedelta) -> int:
    return int(delta.total_seconds() * 1000)


def _slot(m: BattleMatch, user_id) -> int:
    if m.player1_id == user_id:
        return 1
    if m.player2_id is not None and m.player2_id == user_id:
        return 2
    raise HTTPException(404, "MATCH_NOT_FOUND")


def _lock_matchmaking(db: Session, stage: str) -> None:
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": f"vizu-battle-mm-{stage}"})


def _locked(db: Session, match_id) -> BattleMatch:
    m = db.execute(select(BattleMatch).where(BattleMatch.id == match_id).with_for_update()).scalar_one_or_none()
    if m is None:
        raise HTTPException(404, "MATCH_NOT_FOUND")
    return m


def open_match(db: Session, user_id) -> BattleMatch | None:
    return db.execute(
        select(BattleMatch).where(or_(BattleMatch.player1_id == user_id, BattleMatch.player2_id == user_id), BattleMatch.status.in_(OPEN))
        .order_by(BattleMatch.created_at.desc()).limit(1)
    ).scalar_one_or_none()


def _ensure_pool(db: Session, stage: str) -> None:
    if questions.pool_size(db, stage) < config.MIN_POOL:
        raise HTTPException(409, "BATTLE_NOT_ENOUGH_WORDS: Bu bosqich uchun hali yetarli rasmli so‘z yo‘q")


def _seen(m: BattleMatch, slot: int, now: datetime) -> None:
    setattr(m, f"p{slot}_seen_at", now)


# ── starting matches ─────────────────────────────────────────────────────────


def _activate(db: Session, m: BattleMatch, now: datetime) -> None:
    m.questions = questions.build(db, m.level, m.rounds, bot=m.mode == "bot")
    m.status = "active"
    m.starts_at = now + timedelta(seconds=config.COUNTDOWN_S)
    m.current_round = 0


def _new(db: Session, user: User, mode: str, stage: str, points: int, now: datetime, room_code: str | None = None) -> BattleMatch:
    m = BattleMatch(mode=mode, status="waiting", level=stage, room_code=room_code, player1_id=user.id, p1_points_start=points,
                    rounds=config.ROUNDS, p1_seen_at=now, questions=[], created_at=now)
    db.add(m)
    db.flush()
    return m


def _join(db: Session, m: BattleMatch, user: User, points: int, now: datetime) -> None:
    m.player2_id = user.id
    m.p2_points_start = points
    m.p2_seen_at = now
    _activate(db, m, now)


def _find_opponent(db: Session, user_id, points: int, stage: str, waiting_since: datetime, now: datetime, exclude=None) -> BattleMatch | None:
    rows = db.execute(
        select(BattleMatch).where(BattleMatch.status == "waiting", BattleMatch.mode == "ranked", BattleMatch.level == stage,
                                  BattleMatch.player1_id != user_id)
        .order_by(BattleMatch.created_at).with_for_update(skip_locked=True)
    ).scalars().all()
    for c in rows:
        if exclude is not None and c.id == exclude:
            continue
        if c.p1_seen_at is None or c.p1_seen_at < now - timedelta(seconds=config.QUEUE_STALE_S):
            c.status = "cancelled"
            c.finished_at = now
            continue
        waited = max((now - waiting_since).total_seconds(), (now - c.created_at).total_seconds())
        window = config.match_window(waited)
        if window is None or abs(c.p1_points_start - points) <= window:
            return c
    return None


def queue(db: Session, user: User) -> dict:
    now = _now()
    current = open_match(db, user.id)
    if current is not None:
        return state(db, current.id, user)
    profile = profiles.get_profile(db, user.id)
    stage = config.stage_for_points(profile.points)
    _ensure_pool(db, stage)
    _lock_matchmaking(db, stage)
    opponent = _find_opponent(db, user.id, profile.points, stage, now, now)
    if opponent is not None:
        _join(db, opponent, user, profile.points, now)
        match_id = opponent.id
    else:
        match_id = _new(db, user, "ranked", stage, profile.points, now).id
    db.commit()
    return state(db, match_id, user)


def practice(db: Session, user: User) -> dict:
    now = _now()
    if open_match(db, user.id) is not None:
        raise HTTPException(409, "MATCH_ALREADY_OPEN")
    profile = profiles.get_profile(db, user.id)
    stage = config.stage_for_points(profile.points)
    _ensure_pool(db, stage)
    m = _new(db, user, "bot", stage, profile.points, now)
    _activate(db, m, now)
    db.commit()
    return state(db, m.id, user)


def create_room(db: Session, user: User) -> dict:
    now = _now()
    if open_match(db, user.id) is not None:
        raise HTTPException(409, "MATCH_ALREADY_OPEN")
    profile = profiles.get_profile(db, user.id)
    stage = config.stage_for_points(profile.points)
    _ensure_pool(db, stage)
    for _ in range(8):
        code = "".join(secrets.choice(ROOM_ALPHABET) for _ in range(6))
        if db.execute(select(BattleMatch.id).where(BattleMatch.room_code == code)).first() is None:
            break
    m = _new(db, user, "private", stage, profile.points, now, room_code=code)
    db.commit()
    return state(db, m.id, user)


def join_room(db: Session, user: User, code: str) -> dict:
    now = _now()
    code = (code or "").strip().upper()
    if open_match(db, user.id) is not None:
        raise HTTPException(409, "MATCH_ALREADY_OPEN")
    m = db.execute(select(BattleMatch).where(BattleMatch.room_code == code, BattleMatch.mode == "private").with_for_update()).scalar_one_or_none()
    if m is None or m.status != "waiting" or m.player1_id == user.id:
        raise HTTPException(404, "ROOM_NOT_FOUND")
    if m.p1_seen_at is None or m.p1_seen_at < now - timedelta(seconds=config.QUEUE_STALE_S * 5):
        raise HTTPException(404, "ROOM_NOT_FOUND")
    profile = profiles.get_profile(db, user.id)
    _join(db, m, user, profile.points, now)
    db.commit()
    return state(db, m.id, user)


# ── the clock ────────────────────────────────────────────────────────────────


def _answers(db: Session, m: BattleMatch, round_no: int) -> dict[int, BattleAnswer]:
    return {a.slot: a for a in db.execute(select(BattleAnswer).where(BattleAnswer.match_id == m.id, BattleAnswer.round_no == round_no)).scalars()}


def _record(db: Session, m: BattleMatch, round_no: int, slot: int, choice: int | None, time_ms: int) -> BattleAnswer:
    q = m.questions[round_no - 1]
    correct = choice is not None and choice == q["c"]
    score = config.round_score(correct, time_ms)
    a = BattleAnswer(match_id=m.id, round_no=round_no, slot=slot, choice=choice, correct=correct, time_ms=time_ms, score=score)
    db.add(a)
    setattr(m, f"p{slot}_score", getattr(m, f"p{slot}_score") + score)
    db.flush()
    return a


def _begin_round(m: BattleMatch, round_no: int, at: datetime) -> None:
    m.current_round = round_no
    m.round_started_at = at
    m.round_ended_at = None


def tick(db: Session, m: BattleMatch, now: datetime) -> None:
    if m.status == "waiting":
        if m.p1_seen_at is None or m.p1_seen_at < now - timedelta(seconds=config.QUEUE_STALE_S * (5 if m.mode == "private" else 1)):
            m.status = "cancelled"
            m.finished_at = now
        return
    if m.status != "active":
        return
    humans = (1,) if m.mode == "bot" else (1, 2)
    stale = [s for s in humans if (getattr(m, f"p{s}_seen_at") or now) < now - timedelta(seconds=config.AFK_S)]
    if stale:
        if len(stale) == len(humans):
            m.status = "cancelled"
            m.finished_at = now
            return
        _finish(db, m, now, "afk", winner_slot=2 if stale[0] == 1 else 1)
        return
    round_ms = config.ROUND_S * 1000
    for _ in range(4 * config.ROUNDS + 4):
        if m.current_round == 0:
            if now < m.starts_at:
                return
            _begin_round(m, 1, m.starts_at)
            continue
        r = m.current_round
        if m.round_ended_at is None:
            answers = _answers(db, m, r)
            bot = m.questions[r - 1].get("bot")
            if bot and 2 not in answers and now >= m.round_started_at + timedelta(milliseconds=bot["at"]):
                answers[2] = _record(db, m, r, 2, bot["choice"], bot["at"])
            if len(answers) == 2:
                m.round_ended_at = m.round_started_at + timedelta(milliseconds=max(a.time_ms for a in answers.values()))
                continue
            if now >= m.round_started_at + timedelta(milliseconds=round_ms + config.ANSWER_GRACE_MS):
                for s in (1, 2):
                    if s not in answers:
                        _record(db, m, r, s, None, round_ms)
                m.round_ended_at = m.round_started_at + timedelta(milliseconds=round_ms)
                continue
            return
        reveal_end = m.round_ended_at + timedelta(seconds=config.REVEAL_S)
        if now < reveal_end:
            return
        if r >= m.rounds:
            _finish(db, m, reveal_end, "normal")
            return
        _begin_round(m, r + 1, reveal_end)


def _finish(db: Session, m: BattleMatch, now: datetime, reason: str, winner_slot: int | None = None) -> None:
    if winner_slot is None:
        winner_slot = 0 if m.p1_score == m.p2_score else (1 if m.p1_score > m.p2_score else 2)
    m.status = "finished"
    m.finished_at = now
    m.winner_slot = winner_slot
    m.finish_reason = reason
    # 2026-11-05: bot matches count for stats and Battle Points too (only the human, slot 1)
    for slot in ((1,) if m.mode == "bot" else (1, 2)):
        user_id = m.player1_id if slot == 1 else m.player2_id
        p = profiles.get_profile(db, user_id, lock=True)
        result = "draw" if winner_slot == 0 else ("win" if winner_slot == slot else "loss")
        if result == "win":
            p.wins += 1
            p.streak += 1
            p.best_streak = max(p.best_streak, p.streak)
        elif result == "loss":
            p.losses += 1
            p.streak = 0
        else:
            p.draws += 1
        p.last_match_at = now
        if m.mode not in config.POINT_MODES:
            continue
        # own score (+1 per correct word, computed on the server) + 3 for the winner; never negative
        delta = config.points_delta(result, getattr(m, f"p{slot}_score"))
        target = p.points + delta
        inserted = db.execute(
            pg_insert(BattlePointsLedger).values(user_id=user_id, match_id=m.id, delta=delta, balance_after=target, reason="match")
            .on_conflict_do_nothing(constraint="uq_battle_points_ledger_event").returning(BattlePointsLedger.id)
        ).first()
        if inserted is not None:
            before = config.rank_index(p.points)
            p.points = target
            setattr(m, f"p{slot}_delta", delta)
            if config.rank_index(target) > before:
                _notify_rank_up(db, user_id, before, config.rank_index(target))


def _notify_rank_up(db: Session, user_id, before: int, after: int) -> None:
    title = config.rank_title(after)
    stage_up = after // 3 > before // 3
    message = (f"{config.STAGES[after // 3]} — {config.STAGE_SUBTITLES[config.STAGES[after // 3]]}. " if stage_up else "") + \
        f"Glückwunsch! Du bist jetzt {title}. / Tabriklaymiz! Yangi darajangiz: {title}."
    # added to the match transaction (the notification repository would commit half-way through _finish)
    db.add(Notification(user_id=user_id, title=f"Neuer Battle-Rang: {title}", message=message, type=TYPE_BATTLE, link_path="/battle"))


# ── player actions ───────────────────────────────────────────────────────────


def answer(db: Session, user: User, match_id, round_no: int, choice: int) -> dict:
    if not 0 <= choice < config.OPTIONS:
        raise HTTPException(422, "CHOICE_INVALID")
    now = _now()
    m = _locked(db, match_id)
    slot = _slot(m, user.id)
    _seen(m, slot, now)
    tick(db, m, now)
    if m.status != "active" or m.current_round != round_no or m.round_ended_at is not None or m.round_started_at is None:
        db.commit()
        raise HTTPException(409, "ROUND_CLOSED")
    if slot in _answers(db, m, round_no):
        db.commit()
        raise HTTPException(409, "ALREADY_ANSWERED")
    elapsed = _ms(now - m.round_started_at)
    _record(db, m, round_no, slot, choice, max(0, min(elapsed, config.ROUND_S * 1000)))
    tick(db, m, now)
    db.commit()
    return state(db, m.id, user)


def leave(db: Session, user: User, match_id) -> dict:
    now = _now()
    m = _locked(db, match_id)
    slot = _slot(m, user.id)
    tick(db, m, now)
    if m.status == "waiting":
        m.status = "cancelled"
        m.finished_at = now
    elif m.status == "active":
        _finish(db, m, now, "forfeit", winner_slot=2 if slot == 1 else 1)
    db.commit()
    return state(db, m.id, user)


def state(db: Session, match_id, user: User) -> dict:
    """The caller's view of the match; also the heartbeat (and, while waiting, re-runs matchmaking)."""
    now = _now()
    m = _locked(db, match_id)
    slot = _slot(m, user.id)
    if m.status in OPEN:
        _seen(m, slot, now)
    if m.status == "waiting" and m.mode == "ranked":
        profile = profiles.get_profile(db, user.id)
        _lock_matchmaking(db, m.level)
        other = _find_opponent(db, user.id, profile.points, m.level, m.created_at, now, exclude=m.id)
        if other is not None:
            m.status = "cancelled"
            m.finished_at = now
            _join(db, other, user, profile.points, now)
            db.commit()
            return state(db, other.id, user)
    tick(db, m, now)
    db.commit()
    return _view(db, m, slot, user, now)


def current(db: Session, user: User) -> dict | None:
    m = open_match(db, user.id)
    return state(db, m.id, user) if m is not None else None


# ── the view ─────────────────────────────────────────────────────────────────


def _iso(d: datetime | None) -> str | None:
    return d.isoformat() if d else None


def _view(db: Session, m: BattleMatch, slot: int, user: User, now: datetime) -> dict:
    other = 2 if slot == 1 else 1
    other_id = m.player2_id if slot == 1 else m.player1_id
    other_user = db.get(User, other_id) if other_id else None
    my_profile = profiles.get_profile(db, user.id)
    other_profile = profiles.get_profile(db, other_id) if other_id else None
    me = {**profiles.player_card(user, my_profile), "score": getattr(m, f"p{slot}_score")}
    opponent = None
    if m.mode == "bot":
        opponent = {**profiles.player_card(None, None), "stage": m.level, "rank": "Trainingspartner", "score": getattr(m, f"p{other}_score")}
    elif other_user is not None:
        opponent = {**profiles.player_card(other_user, other_profile), "score": getattr(m, f"p{other}_score")}

    out = {
        "id": str(m.id), "mode": m.mode, "status": m.status, "stage": m.level, "server_time": now.isoformat(),
        "room_code": m.room_code if m.mode == "private" and m.status == "waiting" else None,
        "waiting_since": _iso(m.created_at) if m.status == "waiting" else None,
        "countdown_ends_at": _iso(m.starts_at), "rounds": m.rounds, "me": me, "opponent": opponent, "round": None, "history": [], "result": None,
        "timing": {"round_s": config.ROUND_S, "reveal_s": config.REVEAL_S, "afk_s": config.AFK_S},
    }
    if m.status in ("active", "finished") and m.current_round:
        rows = db.execute(select(BattleAnswer).where(BattleAnswer.match_id == m.id).order_by(BattleAnswer.round_no)).scalars().all()
        by_round: dict[int, dict[int, BattleAnswer]] = {}
        for a in rows:
            by_round.setdefault(a.round_no, {})[a.slot] = a
        closed = m.current_round if (m.round_ended_at is not None or m.status == "finished") else m.current_round - 1
        out["history"] = [
            {"round": r, "me": by_round.get(r, {}).get(slot).correct if by_round.get(r, {}).get(slot) else None,
             "opponent": by_round.get(r, {}).get(other).correct if by_round.get(r, {}).get(other) else None}
            for r in range(1, closed + 1)
        ]
        if m.status == "active":
            out["round"] = _round_view(db, m, slot, other, by_round.get(m.current_round, {}), now)
    if m.status == "finished":
        out["result"] = _result_view(m, slot)
    return out


def _round_view(db: Session, m: BattleMatch, slot: int, other: int, answers: dict[int, BattleAnswer], now: datetime) -> dict:
    r = m.current_round
    q = m.questions[r - 1]
    ids = [q["w"], *q["opts"]]
    words = {str(w.id): w for w in db.execute(select(BattleWord).where(BattleWord.id.in_(ids))).scalars()}
    target = words.get(q["w"])
    revealed = m.round_ended_at is not None
    mine = answers.get(slot)
    view = {
        "no": r, "total": m.rounds, "phase": "reveal" if revealed else "question",
        "started_at": _iso(m.round_started_at), "deadline": _iso(m.round_started_at + timedelta(seconds=config.ROUND_S)),
        "reveal_ends_at": _iso(m.round_ended_at + timedelta(seconds=config.REVEAL_S)) if revealed else None,
        "image_url": f"/api/v1/battle/media/{media.round_token(m.id, r, now.timestamp())}",
        "category": (questions.categories().get(target.category) if target else None),
        "options": [words[i].display if i in words else "—" for i in q["opts"]],
        "my_answer": {"choice": mine.choice, "correct": mine.correct, "score": mine.score, "time_ms": mine.time_ms} if mine else None,
        "opponent_answered": other in answers,
        "correct": None, "translation": None, "opponent_choice": None,
    }
    if revealed:
        view["correct"] = q["c"]
        view["translation"] = target.translation if target else None
        theirs = answers.get(other)
        view["opponent_choice"] = theirs.choice if theirs else None
    return view


def _result_view(m: BattleMatch, slot: int) -> dict:
    start = m.p1_points_start if slot == 1 else m.p2_points_start
    delta = m.p1_delta if slot == 1 else m.p2_delta
    before, after = config.rank_info(start), config.rank_info(start + delta)
    outcome = "draw" if m.winner_slot == 0 else ("win" if m.winner_slot == slot else "loss")
    earns = m.mode in config.POINT_MODES
    return {
        "outcome": outcome, "reason": m.finish_reason,
        "ranked": earns,  # "earns Battle Points" (ranked or bot); private rooms do not
        "match_score": getattr(m, f"p{slot}_score"), "win_bonus": config.win_bonus(outcome) if earns else 0,
        "points_delta": delta, "points_after": start + delta,
        "rank_before": before, "rank_after": after, "rank_up": after["index"] > before["index"], "stage_up": after["stage"] != before["stage"] and after["index"] > before["index"],
    }


def media_for(db: Session, token: str):
    match_id, round_no = media.read_token(token)
    m = db.get(BattleMatch, match_id)
    if m is None or not 1 <= round_no <= len(m.questions or []):
        raise HTTPException(404, "NOT_FOUND")
    from app.models.battle import BattleImage

    img = db.get(BattleImage, m.questions[round_no - 1]["img"])
    if img is None:
        raise HTTPException(404, "NOT_FOUND")
    return media.serve(media.safe_path(media.IMAGE_ROOT, img.storage_name))
