from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models import Reaction


@runtime_checkable
class RendererAdapter(Protocol):
    async def play(self, reaction: Reaction) -> None: ...

    async def health(self) -> bool: ...
