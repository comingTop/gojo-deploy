from __future__ import annotations

import time
from typing import Awaitable, Callable


class IdleWatchdog:
    """Bill protection: fire ``on_idle`` once after ``idle_seconds`` with no activity.

    ``touch()`` is called whenever the live is active (a gift, a Telegram command).
    If nothing touches it for ``idle_seconds``, ``check()`` fires the stop callback
    exactly once (until the next ``touch``). Clock is injected for deterministic tests.
    """

    def __init__(
        self,
        idle_seconds: float,
        on_idle: Callable[[], Awaitable[None]],
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self.idle_seconds = idle_seconds
        self._on_idle = on_idle
        self._now = now
        self._last = now()
        self._fired = False

    def touch(self) -> None:
        self._last = self._now()
        self._fired = False

    def should_fire(self) -> bool:
        return (not self._fired) and (self._now() - self._last >= self.idle_seconds)

    async def check(self) -> bool:
        if self.should_fire():
            self._fired = True
            await self._on_idle()
            return True
        return False
