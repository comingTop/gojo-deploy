from __future__ import annotations

from .engine import ReactionEngine
from .models import Reaction
from .sources.base import GiftSource


async def run_session(source: GiftSource, engine: ReactionEngine) -> list[Reaction]:
    fired: list[Reaction] = []
    async for event in source.stream():
        reaction = await engine.handle_gift(event)
        if reaction is not None:
            fired.append(reaction)
    return fired
