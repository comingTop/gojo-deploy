from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import AsyncIterator

from ..models import GiftEvent


class SimulatedGiftSource:
    """Replays a scripted list of GiftEvents. Phase-1 stand-in for TikTok."""

    def __init__(self, events: list[GiftEvent], delay_s: float = 0.0) -> None:
        self._events = events
        self._delay_s = delay_s

    async def stream(self) -> AsyncIterator[GiftEvent]:
        for ev in self._events:
            if self._delay_s:
                await asyncio.sleep(self._delay_s)
            yield ev

    @classmethod
    def from_json(cls, path: str | Path, delay_s: float = 0.0) -> "SimulatedGiftSource":
        rows = json.loads(Path(path).read_text(encoding="utf-8"))
        events = [GiftEvent(**row) for row in rows]
        return cls(events, delay_s=delay_s)
