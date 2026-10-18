from __future__ import annotations

from pathlib import Path

from orchestrator.adapters.mock import MockAdapter
from orchestrator.config import load_config
from orchestrator.coordinator import run_live_session
from orchestrator.engine import ReactionEngine
from orchestrator.sources.simulated import SimulatedGiftSource
from orchestrator.state import StateStore

CONFIG = Path(__file__).resolve().parents[1] / "config" / "reactions.json"
FIX = Path(__file__).resolve().parent / "fixtures" / "gifts.json"


class FakeOverlay:
    def __init__(self) -> None:
        self.msgs: list[dict] = []

    async def broadcast(self, message: dict) -> None:
        self.msgs.append(message)

    def by_type(self, t: str) -> list[dict]:
        return [m for m in self.msgs if m.get("type") == t]


class FakeVoice:
    def __init__(self) -> None:
        self.played: list[str] = []

    async def play(self, reaction) -> None:
        self.played.append(reaction.id)


class FakeWatchdog:
    def __init__(self) -> None:
        self.touches = 0

    def touch(self) -> None:
        self.touches += 1


async def test_coordinator_fans_out_to_overlay_voice_watchdog(clock):
    cfg = load_config(CONFIG)
    engine = ReactionEngine(cfg, MockAdapter(), StateStore(), now=clock)
    overlay, voice, wd = FakeOverlay(), FakeVoice(), FakeWatchdog()

    class Ticking(SimulatedGiftSource):
        async def stream(self):
            async for ev in super().stream():
                clock.advance(60.0)  # avoid cooldown/pace blocking distinct reactions
                yield ev

    await run_live_session(Ticking.from_json(FIX), engine, overlay, voice=voice, watchdog=wd)

    # fixture has 5 events; 4 of them fire reactions (one is a mid-combo tick)
    assert len(overlay.by_type("top3")) == 5           # TOP-3 refreshed per gift
    assert len(overlay.by_type("cue")) == 4            # menu flash per reaction
    assert voice.played == ["flash", "flash", "roxo", "dominio"]
    assert wd.touches == 4                             # watchdog touched per reaction
