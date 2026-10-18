from __future__ import annotations

import asyncio
from typing import Protocol


class ObsLike(Protocol):
    async def start_stream(self) -> None: ...
    async def stop_stream(self) -> None: ...
    def is_streaming(self) -> bool: ...


class ObsController:
    """obs-websocket v5 wrapper (lazy import of obsws-python).

    Lets the Telegram bot start/stop the RTMP stream to TikTok programmatically —
    the real "liga/desliga". Network/GUI-bound, so it is injected into the
    LiveController as an ``ObsLike`` and swapped for a fake in tests.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 4455, password: str = "") -> None:
        self._cfg = (host, port, password)
        self._client = None
        self._streaming = False

    def _ensure(self):
        if self._client is None:
            import obsws_python as obs  # lazy: only needed on the real host

            host, port, password = self._cfg
            self._client = obs.ReqClient(host=host, port=port, password=password)
        return self._client

    async def start_stream(self) -> None:
        await asyncio.to_thread(lambda: self._ensure().start_stream())
        self._streaming = True

    async def stop_stream(self) -> None:
        await asyncio.to_thread(lambda: self._ensure().stop_stream())
        self._streaming = False

    def is_streaming(self) -> bool:
        return self._streaming
