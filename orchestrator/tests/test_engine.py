from __future__ import annotations

from pathlib import Path

from orchestrator.adapters.mock import MockAdapter
from orchestrator.config import load_config
from orchestrator.engine import ReactionEngine
from orchestrator.models import GiftEvent
from orchestrator.state import StateStore

CONFIG = Path(__file__).resolve().parents[1] / "config" / "reactions.json"


def _engine(clock):
    cfg = load_config(CONFIG)
    adapter = MockAdapter()
    engine = ReactionEngine(cfg, adapter, StateStore(), now=clock)
    return cfg, adapter, engine


def _rose(ts=1.0, count=1, combo_end=True):
    return GiftEvent("u1", "lucas", 5655, "Rose", 1, count, ts, is_combo_end=combo_end)


async def test_matching_rose_fires_flash(clock):
    _, adapter, engine = _engine(clock)
    r = await engine.handle_gift(_rose())
    assert r is not None and r.id == "flash"
    assert [x.id for x in adapter.played] == ["flash"]


async def test_intermediate_combo_tick_does_not_fire(clock):
    _, adapter, engine = _engine(clock)
    assert await engine.handle_gift(_rose(combo_end=False)) is None
    assert adapter.played == []


async def test_per_reaction_cooldown_blocks_repeat(clock):
    _, adapter, engine = _engine(clock)
    await engine.handle_gift(_rose())            # fires flash (cooldown 6s)
    clock.advance(1.0)
    assert await engine.handle_gift(_rose()) is None   # still cooling down
    clock.advance(6.0)
    assert (await engine.handle_gift(_rose())).id == "flash"  # cooldown elapsed


async def test_global_min_interval_blocks_cross_reaction_spam(clock):
    cfg, adapter, engine = _engine(clock)
    universe = GiftEvent("u4", "david", 9999, "Universe", 1000, 1, 9.0)
    galaxy = GiftEvent("u3", "bia", 8888, "Galaxy", 100, 1, 9.1)
    assert (await engine.handle_gift(universe)).id == "dominio"
    # within global_min_interval_s (1.5s) a different reaction is paced out
    assert await engine.handle_gift(galaxy) is None


async def test_gift_is_recorded_even_when_no_reaction(clock):
    _, _, engine = _engine(clock)
    # coins below every tier and no matching name => no reaction, but recorded
    unknown = GiftEvent("u9", "ghost", 1, "UnknownGift", 0, 1, 50.0)
    assert await engine.handle_gift(unknown) is None
    assert engine.state.top_gifters(3, 50.0) == [("ghost", 0)]
