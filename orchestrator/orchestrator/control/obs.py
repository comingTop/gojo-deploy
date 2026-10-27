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

    def _output_active(self, client) -> bool:
        # OBS returns request code 501 if you start/stop streaming while the
        # output is already in the target state. In the LIVE Studio setup OBS
        # only runs the Virtual Camera and never RTMP-streams, so a blind
        # stop_stream() would always 501 and, unhandled, kill the event loop.
        try:
            return bool(getattr(client.get_stream_status(), "output_active", False))
        except Exception:
            return False

    async def start_stream(self) -> None:
        def _start() -> None:
            client = self._ensure()
            try:
                if not self._output_active(client):
                    client.start_stream()
            except Exception:
                pass

        await asyncio.to_thread(_start)
        self._streaming = True

    async def stop_stream(self) -> None:
        def _stop() -> None:
            client = self._ensure()
            try:
                if self._output_active(client):
                    client.stop_stream()
            except Exception:
                pass

        await asyncio.to_thread(_stop)
        self._streaming = False

    def is_streaming(self) -> bool:
        return self._streaming
