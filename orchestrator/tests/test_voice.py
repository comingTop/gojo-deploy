from __future__ import annotations

from orchestrator.models import ActionSpec, Reaction
from orchestrator.voice.player import VoicePlayer


def _reaction(clip: str | None) -> Reaction:
    return Reaction("roxo", "Roxo", ActionSpec("explode", {}), clip, None, 1.0)


async def test_player_resolves_clip_under_root_and_calls_backend():
    calls: list[str] = []
    vp = VoicePlayer(root="/app", play_fn=lambda p: calls.append(p))
    await vp.play(_reaction("voice/output/roxo.wav"))
    assert calls == ["/app/voice/output/roxo.wav"]


async def test_player_skips_reaction_without_clip():
    calls: list[str] = []
    vp = VoicePlayer(play_fn=lambda p: calls.append(p))
    await vp.play(_reaction(None))
    assert calls == []


async def test_player_awaits_async_backend():
    seen: list[str] = []

    async def backend(path: str) -> None:
        seen.append(path)

    vp = VoicePlayer(root=".", play_fn=backend)
    await vp.play(_reaction("voice/output/flash.wav"))
    assert seen and seen[0].endswith("flash.wav")
