from __future__ import annotations

from ..models import Reaction


class MockAdapter:
    """Records dispatched reactions; used for headless engine tests."""

    def __init__(self, fail: bool = False) -> None:
        self.played: list[Reaction] = []
        self.fail = fail

    async def play(self, reaction: Reaction) -> None:
        if self.fail:
            raise RuntimeError("renderer down")
        self.played.append(reaction)

    async def health(self) -> bool:
        return not self.fail
