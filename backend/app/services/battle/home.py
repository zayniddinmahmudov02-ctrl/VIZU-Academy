"""Battle home: everything the Battle start page shows in one response."""

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.battle import config, engine, profiles, questions, themes


def home(db: Session, user: User) -> dict:
    p = profiles.get_profile(db, user.id)
    db.commit()
    rank = config.rank_info(p.points)
    open_match = engine.open_match(db, user.id)
    board = profiles.leaderboard(db, user, page=1, size=5)
    pool = questions.pool_size(db, rank["stage"])
    return {
        "player": profiles.player_card(user, p), "rank": rank, "stats": profiles.stats(p), "achievements": profiles.achievements(p),
        "avatars": profiles.avatars(p), "recent": profiles.recent_matches(db, user, 6),
        "leaderboard": {"items": board["items"], "me": board["me"]},
        "ladder": [{"index": i, "title": config.rank_title(i), "stage": config.STAGES[i // 3], "at": i * config.RANK_STEP}
                   for i in range(len(config.STAGES) * 3)],
        "theme": themes.for_stage(db, rank["stage"]), "themes": themes.public_list(db),
        "open_match_id": str(open_match.id) if open_match else None,
        "playable": pool >= config.MIN_POOL, "pool": pool, "min_pool": config.MIN_POOL,
        "rules": {"rounds": config.ROUNDS, "round_s": config.ROUND_S, "base": config.BASE_SCORE, "speed_bonus": config.SPEED_BONUS,
                  "win": config.WIN_POINTS, "draw": config.DRAW_POINTS, "loss": config.LOSS_POINTS},
    }
