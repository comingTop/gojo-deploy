from __future__ import annotations

from types import SimpleNamespace

from orchestrator.sources.normalize import normalize_gift


def _event(name="Rose", gid=5655, coins=1, count=1, streaking=False,
           uid="7", nick="lucas"):
    """Stand-in shaped like a TikTokLive v7 GiftEvent (duck-typed)."""
    return SimpleNamespace(
        gift=SimpleNamespace(name=name, id=gid, diamond_count=coins, streakable=count > 1),
        user=SimpleNamespace(id=uid, nickname=nick, display_id=f"{nick}_handle"),
        repeat_count=count,
        gift_id=gid,
        streaking=streaking,
    )


def test_single_gift_maps_all_fields():
    g = normalize_gift(_event(), now=lambda: 100.0)
    assert (g.gift_name, g.gift_id, g.coins, g.count) == ("Rose", 5655, 1, 1)
    assert g.username == "lucas" and g.user_id == "7"
    assert g.timestamp == 100.0
    assert g.is_combo_end is True  # not streaking


def test_mid_combo_tick_is_not_combo_end():
    g = normalize_gift(_event(count=3, streaking=True))
    assert g.is_combo_end is False
    assert g.count == 3


def test_combo_end_carries_total_count_and_coins():
    g = normalize_gift(_event(coins=1, count=5, streaking=False))
    assert g.is_combo_end is True
    assert g.count == 5
    assert g.total_coins == 5


def test_username_falls_back_to_display_id():
    ev = _event(nick="")
    ev.user.nickname = ""  # no display name
    g = normalize_gift(ev)
    assert g.username == "_handle"  # display_id fallback, never empty


def test_high_value_gift_coins():
    g = normalize_gift(_event(name="Universe", gid=9999, coins=1000, count=1))
    assert g.gift_name == "Universe" and g.total_coins == 1000
