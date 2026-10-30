import json
import random
from datetime import date, timedelta

from app.config import BASE_DIR

POOL = json.loads((BASE_DIR / "data" / "task_pool.json").read_text())
GROUPS = ["health", "mind", "social"]


def tasks_for(user_id: int, day: date) -> list[dict]:
    rng = random.Random(f"{user_id}-{day.isoformat()}")
    picked = [rng.choice([t for t in POOL if t["group"] == g]) for g in GROUPS]
    extra = [t for t in POOL if t not in picked]
    return picked + [rng.choice(extra)]


def streak(done_days: set[date], today: date) -> int:
    """Days in a row with at least one task done, counting back from today (or yesterday)."""
    day = today if today in done_days else today - timedelta(days=1)
    count = 0
    while day in done_days:
        count += 1
        day -= timedelta(days=1)
    return count