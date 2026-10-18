from __future__ import annotations

from ..models import Reaction


def _entries(rows: list[tuple[str, int]]) -> list[dict]:
    return [{"rank": i + 1, "username": u, "coins": c} for i, (u, c) in enumerate(rows)]


def top3_message(top3: list[tuple[str, int]]) -> dict:
    """Leaderboard update sent to the TOP-3 browser source."""
    return {"type": "top3", "entries": _entries(top3)}


def ranking_message(ranking: list[tuple[str, int]], day: str) -> dict:
    """Daily-ranking update (resets with the day key)."""
    return {"type": "ranking", "day": day, "entries": _entries(ranking)}


def reaction_cue_message(reaction: Reaction) -> dict:
    """Tells the gift-menu overlay which action just fired, so it can flash it."""
    return {
        "type": "cue",
        "id": reaction.id,
        "label": reaction.label,
        "action": reaction.action.command,
    }
