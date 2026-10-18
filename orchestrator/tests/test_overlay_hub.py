from __future__ import annotations

import asyncio
import json

import websockets

from orchestrator.overlay.hub import OverlayHub


async def _serve(hub: OverlayHub):
    server = await hub.serve("127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return server, f"ws://127.0.0.1:{port}"


async def test_hub_broadcasts_to_connected_client():
    hub = OverlayHub()
    server, url = await _serve(hub)
    try:
        async with websockets.connect(url) as ws:
            await asyncio.sleep(0.05)  # let the handler register the client
            await hub.broadcast({"type": "top3", "entries": []})
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
            assert msg["type"] == "top3"
    finally:
        server.close()
        await server.wait_closed()


async def test_hub_replays_last_state_on_connect():
    hub = OverlayHub()
    server, url = await _serve(hub)
    try:
        await hub.broadcast({"type": "top3",
                             "entries": [{"rank": 1, "username": "david", "coins": 1000}]})
        async with websockets.connect(url) as ws:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
            assert msg["entries"][0]["username"] == "david"
    finally:
        server.close()
        await server.wait_closed()
