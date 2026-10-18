from __future__ import annotations

import time
from typing import Callable

from .adapters.base import RendererAdapter
from .config import AppConfig, ReactionConfig
from .models import GiftEvent, Reaction
from .state import StateStore


class ReactionEngine:
    def __init__(
        self,
        config: AppConfig,
        adapter: RendererAdapter,
        state: StateStore,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self.config = config
        self.adapter = adapter
        self.state = state
        self._now = now
        self._last_fired: dict[str, float] = {}
        self._last_any_fired: float = float("-inf")

    def match(self, event: GiftEvent) -> ReactionConfig | None:
        for rc in self.config.reactions:
            if rc.gift.matches(event.gift_name, event.gift_id, event.total_coins):
                return rc
        return None

    async def handle_gift(self, event: GiftEvent) -> Reaction | None:
        if not event.is_combo_end:
            return None
        self.state.record_gift(event.user_id, event.username, event.total_coins, event.timestamp)
        rc = self.match(event)
        if rc is None:
            return None
        t = self._now()
        if t - self._last_fired.get(rc.id, float("-inf")) < rc.cooldown_s:
            return None
        if t - self._last_any_fired < self.config.global_min_interval_s:
            return None
        reaction = rc.to_reaction()
        await self.adapter.play(reaction)
        self._last_fired[rc.id] = t
        self._last_any_fired = t
        return reaction
