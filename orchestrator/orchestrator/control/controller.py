from __future__ import annotations

import time
from typing import Awaitable, Callable

from ..engine import ReactionEngine
from .obs import ObsLike


class LiveController:
    """Operations the Telegram bot invokes: start/stop the live, status, test a
    reaction. Holds the engine (reaction on/off) and an OBS controller (stream
    on/off), plus an optional VM-stop callback for bill protection.
    """

    def __init__(
        self,
        engine: ReactionEngine,
        obs: ObsLike,
        vm_stop: Callable[[], Awaitable[None]] | None = None,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self.engine = engine
        self.obs = obs
        self._vm_stop = vm_stop
        self._now = now
        self.started_at: float | None = None

    @property
    def live(self) -> bool:
        return self.engine.enabled

    async def start_live(self) -> str:
        self.engine.enabled = True
        await self.obs.start_stream()
        self.started_at = self._now()
        return "🔴 Live ligada — o Gojo já está reagindo aos presentes."

    async def stop_live(self, stop_vm: bool = False) -> str:
        self.engine.enabled = False
        await self.obs.stop_stream()
        msg = "🛑 Live desligada."
        if stop_vm and self._vm_stop is not None:
            await self._vm_stop()
            msg += " Desligando a máquina para não gastar à toa."
        return msg

    async def test_reaction(self, reaction_id: str) -> str:
        for rc in self.engine.config.reactions:
            if rc.id == reaction_id:
                await self.engine.adapter.play(rc.to_reaction())
                return f"✅ Testando: {rc.label}"
        return f"❓ Reação '{reaction_id}' não encontrada."

    def status(self) -> dict:
        return {
            "live": self.engine.enabled,
            "obs_streaming": self.obs.is_streaming(),
            "top3": self.engine.state.top_gifters(3, time.time()),
        }
