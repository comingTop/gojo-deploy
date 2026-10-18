from __future__ import annotations

from orchestrator.models import ActionSpec, GiftEvent, Reaction


def test_gift_event_total_coins_multiplies_count():
    ev = GiftEvent(user_id="u1", username="lucas", gift_id=5655,
                   gift_name="Rose", coins=1, count=5, timestamp=1000.0)
    assert ev.total_coins == 5
    assert ev.is_combo_end is True  # default


def test_models_are_frozen():
    a = ActionSpec(command="explode", params={"radius": 15})
    r = Reaction(id="roxo", label="Hollow Purple", action=a,
                 voice_clip="voice/output/roxo.wav", overlay_cue="menu.roxo",
                 cooldown_s=8.0)
    assert r.action.params["radius"] == 15
    try:
        r.cooldown_s = 1.0  # type: ignore[misc]
        assert False, "Reaction must be immutable"
    except Exception:
        pass
