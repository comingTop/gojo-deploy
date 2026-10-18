from __future__ import annotations

import asyncio
import json

import websockets


class OverlayHub:
    """WebSocket fan-out for the OBS browser-source overlays.

    The orchestrator calls ``broadcast()`` whenever state changes (a reaction fires,
    the TOP-3 or daily ranking updates). Each overlay page connects once and receives
    the latest snapshot immediately, then live updates. Overlays are receive-only.
    """

    def __init__(self) -> None:
        self._clients: set = set()
        # last message per type, replayed to a client the moment it connects so an
        # overlay that loads mid-stream shows correct state instead of blank.
        self._last: dict[str, dict] = {}
        self._server = None

    async def _handler(self, ws, *args) -> None:  # *args tolerates websockets API versions
        self._clients.add(ws)
        try:
            for message in self._last.values():
                await ws.send(json.dumps(message))
            async for _ in ws:
                pass  # ignore anything a client sends
        finally:
            self._clients.discard(ws)

    async def serve(self, host: str = "127.0.0.1", port: int = 8765):
        self._server = await websockets.serve(self._handler, host, port)
        return self._server

    async def broadcast(self, message: dict) -> None:
        mtype = message.get("type", "")
        if mtype:
            self._last[mtype] = message
        if not self._clients:
            return
        data = json.dumps(message)
        await asyncio.gather(
            *(client.send(data) for client in list(self._clients)),
            return_exceptions=True,
        )
