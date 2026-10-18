from __future__ import annotations

from pathlib import Path

from orchestrator.adapters.mock import MockAdapter
from orchestrator.config import load_config
from orchestrator.control.commands import handle_command
from orchestrator.control.controller import LiveController
from orchestrator.control.watchdog import IdleWatchdog
from orchestrator.engine import ReactionEngine
from orchestrator.models import GiftEvent
from orchestrator.state import StateStore

CONFIG = Path(__file__).resolve().parents[1] / "config" / "reactions.json"


class FakeObs:
    def __init__(self) -> None:
        self.started = 0
        self.stopped = 0
        self._streaming = False

    async def start_stream(self) -> None:
        self.started += 1
        self._streaming = True

    async def stop_stream(self) -> None:
        self.stopped += 1
        self._streaming = False

    def is_streaming(self) -> bool:
        return self._streaming


def _engine():
    cfg = load_config(CONFIG)
    return ReactionEngine(cfg, MockAdapter(), StateStore(), now=lambda: 0.0)


def _rose():
    return GiftEvent("u1", "lucas", 5655, "Rose", 1, 1, 1.0)


# --- engine on/off gate -----------------------------------------------------

async def test_disabled_engine_ignores_gifts():
    engine = _engine()
    engine.enabled = False
    assert await engine.handle_gift(_rose()) is None
    assert engine.adapter.played == []


# --- LiveController ---------------------------------------------------------

async def test_start_and_stop_toggle_engine_and_obs():
    engine, obs = _engine(), FakeObs()
    ctrl = LiveController(engine, obs)
    await ctrl.start_live()
    assert engine.enabled is True and obs.is_streaming() is True and obs.started == 1
    await ctrl.stop_live()
    assert engine.enabled is False and obs.is_streaming() is False and obs.stopped == 1


async def test_stop_live_triggers_vm_stop_for_bill_protection():
    engine, obs = _engine(), FakeObs()
    stopped = []
    ctrl = LiveController(engine, obs, vm_stop=lambda: _append(stopped))
    await ctrl.stop_live(stop_vm=True)
    assert stopped == ["vm"]


async def _append(box):
    box.append("vm")


async def test_test_reaction_plays_known_reaction():
    engine, obs = _engine(), FakeObs()
    ctrl = LiveController(engine, obs)
    msg = await ctrl.test_reaction("roxo")
    assert "Hollow Purple" in msg
    assert [r.id for r in engine.adapter.played] == ["roxo"]


# --- command dispatcher + auth ----------------------------------------------

async def test_ligar_desligar_commands():
    engine, obs = _engine(), FakeObs()
    ctrl = LiveController(engine, obs)
    assert "ligada" in (await handle_command("/ligar", 1, ctrl, {1}))
    assert engine.enabled is True
    assert "desligada" in (await handle_command("/desligar", 1, ctrl, {1}))
    assert engine.enabled is False


async def test_unauthorized_chat_is_ignored():
    engine, obs = _engine(), FakeObs()
    ctrl = LiveController(engine, obs)
    assert await handle_command("/ligar", 999, ctrl, {1}) is None
    assert engine.enabled is True  # untouched (default), stream not started
    assert obs.started == 0


async def test_status_reports_live_and_top3():
    engine, obs = _engine(), FakeObs()
    engine.state.record_gift("u4", "david", 1000, 1_770_000_000.0)
    ctrl = LiveController(engine, obs)
    out = await handle_command("/status", 1, ctrl, {1})
    assert "Live:" in out and "TOP 3" in out


# --- IdleWatchdog -----------------------------------------------------------

async def test_watchdog_fires_once_after_idle():
    t = {"v": 0.0}
    fired = []
    wd = IdleWatchdog(10.0, on_idle=lambda: _mark(fired), now=lambda: t["v"])
    assert await wd.check() is False       # not idle yet
    t["v"] = 10.0
    assert await wd.check() is True         # idle -> fires
    assert await wd.check() is False        # does not fire again
    assert fired == ["idle"]


async def test_watchdog_touch_resets_timer():
    t = {"v": 0.0}
    fired = []
    wd = IdleWatchdog(10.0, on_idle=lambda: _mark(fired), now=lambda: t["v"])
    t["v"] = 9.0
    wd.touch()               # activity at t=9
    t["v"] = 15.0            # only 6s since touch
    assert await wd.check() is False
    assert fired == []


async def _mark(box):
    box.append("idle")
