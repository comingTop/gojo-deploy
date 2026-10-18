from __future__ import annotations

import asyncio
import inspect
from pathlib import Path
from typing import Callable

from ..models import Reaction


class VoicePlayer:
    """Plays a reaction's pre-generated wav line.

    On the host the audio is routed to a virtual device (VB-CABLE) that OBS
    captures, so Gojo's voice goes into the stream; ``device`` selects it by name.
    ``voice_clip`` paths are resolved relative to ``root``. A ``play_fn`` can be
    injected for tests. Implements the coordinator's VoicePlayer protocol.
    """

    def __init__(
        self,
        root: str = ".",
        device: str | None = None,
        play_fn: Callable[[str], object] | None = None,
    ) -> None:
        self.root = Path(root)
        self.device = device
        self._play_fn = play_fn

    async def play(self, reaction: Reaction) -> None:
        if not reaction.voice_clip:
            return
        path = str(self.root / reaction.voice_clip)
        if self._play_fn is not None:
            result = self._play_fn(path)
            if inspect.isawaitable(result):
                await result
            return
        await asyncio.to_thread(self._play_wav, path)

    def _play_wav(self, path: str) -> None:
        import sounddevice as sd  # lazy: only needed on the host
        import soundfile as sf

        data, samplerate = sf.read(path, dtype="float32")
        sd.play(data, samplerate, device=self.device)
        sd.wait()
