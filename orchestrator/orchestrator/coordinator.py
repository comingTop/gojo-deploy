from __future__ import annotations

import time
from typing import Awaitable, Callable, Protocol

from .engine import ReactionEngine
from .models import Reaction
from .overlay.hub import OverlayHub
from .overlay.messages import reaction_cue_message, top3_message
from .sources.base import GiftSource


class VoicePlayer(Protocol):
    async def play(self, reaction: Reaction) -> None: ...


class Touchable(Protocol):
    def touch(self) -> None: ...


async def run_live_session(
    source: GiftSource,
    engine: ReactionEngine,
    overlay: OverlayHub,
    *,
    voice: VoicePlayer | None = None,
    watchdog: Touchable | None = None,
    now: Callable[[], float] = time.time,
) -> None:
    """The real run loop: consume gifts, drive reactions, and fan presentation out.

    For every gift the TOP-3 overlay is refreshed; when a reaction fires, the menu
    overlay gets a flash cue, the Gojo voice line plays, and the idle watchdog is
    touched (so an active live never auto-stops). Swapping the source (TikTok vs
    simulated) or the engine's adapter (GTA vs mock) does not change this loop.
    """
    async for event in source.stream():
        reaction = await engine.handle_gift(event)
        # Diagnostic: every gift's exact name+id as TikTok sends it, so an
        # unmapped gift (e.g. a locale-named "Mini dino") can be mapped by id.
        print(f"[gift] name={event.gift_name!r} id={event.gift_id} "
              f"coins={event.total_coins} user={event.username!r} "
              f"-> {reaction.id if reaction else 'NO MATCH'}", flush=True)
        await overlay.broadcast(top3_message(engine.state.top_gifters(3, now())))
        if reaction is not None:
            await overlay.broadcast(reaction_cue_message(reaction))
            if voice is not None:
                await voice.play(reaction)
            if watchdog is not None:
                watchdog.touch()
