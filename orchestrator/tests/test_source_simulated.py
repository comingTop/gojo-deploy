from __future__ import annotations

from pathlib import Path

from orchestrator.models import GiftEvent
from orchestrator.sources.simulated import SimulatedGiftSource

FIX = Path(__file__).resolve().parent / "fixtures" / "gifts.json"


async def _drain(src) -> list[GiftEvent]:
    return [ev async for ev in src.stream()]


async def test_simulated_source_yields_in_order():
    events = [
        GiftEvent("u1", "lucas", 5655, "Rose", 1, 1, 1.0),
        GiftEvent("u2", "bia", 9999, "Universe", 1000, 1, 2.0),
    ]
    out = await _drain(SimulatedGiftSource(events))
    assert [e.gift_name for e in out] == ["Rose", "Universe"]


async def test_simulated_source_from_json_fixture():
    out = await _drain(SimulatedGiftSource.from_json(FIX))
    assert len(out) >= 3
    assert any(e.gift_name == "Universe" for e in out)
    # the fixture includes a combo: intermediate ticks marked is_combo_end=False
    assert any(e.is_combo_end is False for e in out)
