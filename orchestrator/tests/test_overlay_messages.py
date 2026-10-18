from __future__ import annotations

from orchestrator.models import ActionSpec, Reaction
from orchestrator.overlay.messages import (
    ranking_message,
    reaction_cue_message,
    top3_message,
)


def test_top3_message_ranks_entries_in_order():
    msg = top3_message([("david", 1000), ("bia", 100)])
    assert msg["type"] == "top3"
    assert msg["entries"][0] == {"rank": 1, "username": "david", "coins": 1000}
    assert msg["entries"][1]["rank"] == 2


def test_reaction_cue_message_carries_id_and_action():
    r = Reaction("roxo", "Hollow Purple", ActionSpec("explode", {"radius": 15}),
                 None, None, 8.0)
    assert reaction_cue_message(r) == {
        "type": "cue", "id": "roxo", "label": "Hollow Purple", "action": "explode",
    }


def test_ranking_message_includes_day_key():
    msg = ranking_message([("david", 1000)], "2026-10-18")
    assert msg["type"] == "ranking"
    assert msg["day"] == "2026-10-18"
    assert msg["entries"][0]["rank"] == 1
