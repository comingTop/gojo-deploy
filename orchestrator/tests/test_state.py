from __future__ import annotations

from datetime import datetime, timezone

from orchestrator.state import StateStore

# 12:00 BRT on two consecutive days (BRT = UTC-3), expressed as UTC timestamps.
NOON_UTC = datetime(2026, 10, 18, 15, 0, tzinfo=timezone.utc).timestamp()   # 12:00 BRT
NEXT_DAY = datetime(2026, 10, 19, 15, 0, tzinfo=timezone.utc).timestamp()   # next day 12:00 BRT


def test_top_gifters_sums_and_ranks_within_day():
    s = StateStore()
    s.record_gift("u1", "lucas", 50, NOON_UTC)
    s.record_gift("u2", "bia", 100, NOON_UTC)
    s.record_gift("u1", "lucas", 70, NOON_UTC)   # lucas now 120 > bia 100
    assert s.top_gifters(3, NOON_UTC) == [("lucas", 120), ("bia", 100)]


def test_daily_ranking_resets_on_new_day():
    s = StateStore()
    s.record_gift("u1", "lucas", 500, NOON_UTC)
    assert s.top_gifters(3, NEXT_DAY) == []          # new day => empty ranking
    s.record_gift("u2", "bia", 10, NEXT_DAY)
    assert s.top_gifters(3, NEXT_DAY) == [("bia", 10)]


def test_day_key_is_local_date():
    s = StateStore()
    assert s.day_key(NOON_UTC) == "2026-10-18"
