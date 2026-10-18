from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from orchestrator.adapters.gta import GtaAdapter
from orchestrator.models import ActionSpec, Reaction


class _Handler(BaseHTTPRequestHandler):
    paths: list[str] = []

    def do_GET(self):  # noqa: N802
        _Handler.paths.append(self.path)
        self.send_response(500 if self.path == "/fail" else 200)
        self.end_headers()

    def log_message(self, *args):  # silence test server logging
        pass


@pytest.fixture
def server():
    _Handler.paths = []
    srv = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}"
    finally:
        srv.shutdown()


def _reaction(command: str, params: dict) -> Reaction:
    return Reaction(id="x", label="X", action=ActionSpec(command, params),
                    voice_clip=None, overlay_cue=None, cooldown_s=1.0)


async def test_play_sends_command_with_single_param(server):
    adapter = GtaAdapter(base_url=server)
    await adapter.play(_reaction("explode", {"radius": 15}))
    assert "/explode:15" in _Handler.paths


async def test_play_joins_multiple_params_in_order(server):
    adapter = GtaAdapter(base_url=server)
    await adapter.play(_reaction("domain_expansion", {"weather": "THUNDER", "attackers": 6}))
    assert "/domain_expansion:THUNDER,6" in _Handler.paths


async def test_play_no_params_sends_bare_command(server):
    adapter = GtaAdapter(base_url=server)
    await adapter.play(_reaction("teleport_fly", {}))
    assert "/teleport_fly" in _Handler.paths


async def test_command_map_renames_endpoint(server):
    adapter = GtaAdapter(base_url=server, command_map={"explode": "boom"})
    await adapter.play(_reaction("explode", {"radius": 15}))
    assert "/boom:15" in _Handler.paths


async def test_health_true_when_plugin_up(server):
    adapter = GtaAdapter(base_url=server)
    assert await adapter.health() is True


async def test_health_false_when_plugin_down():
    adapter = GtaAdapter(base_url="http://127.0.0.1:1")  # nothing listening
    assert await adapter.health() is False
