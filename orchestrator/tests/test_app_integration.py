from __future__ import annotations

from pathlib import Path

from orchestrator.adapters.mock import MockAdapter
from orchestrator.app import run_session
from orchestrator.config import load_config
from orchestrator.engine import ReactionEngine
from orchestrator.sources.simulated import SimulatedGiftSource
from orchestrator.state import StateStore

CONFIG = Path(__file__).resolve().parents[1] / "config" / "reactions.json"
FIX = Path(__file__).resolve().parent / "fixtures" / "gifts.json"


async def test_full_simulated_session(clock):
    cfg = load_config(CONFIG)
    adapter = MockAdapter()
    engine = ReactionEngine(cfg, adapter, StateStore(), now=clock)

    # advance the injected clock between events so cooldown/pace don't block the
    # distinct reactions in the fixture; simulated source has no real delay.
    class Ticking(SimulatedGiftSource):
        async def stream(self):
            async for ev in super().stream():
                clock.advance(60.0)
                yield ev

    fired = await run_session(Ticking.from_json(FIX), engine)
    # fixture: Rose(combo tick, ignored) -> Rose(combo end) -> Galaxy -> Universe
    assert [r.id for r in fired] == ["flash", "flash", "roxo", "dominio"]
    # david(Universe,1000) tops the day
    assert engine.state.top_gifters(1, 9.0)[0][0] == "david"
