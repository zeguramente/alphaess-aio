import asyncio
from dataclasses import dataclass, field
from typing import Any

import pytest
from aiohttp import web

from alphaessaio import AlphaEssAPI, AlphaEssAuth
from tests.helpers import DOC_APP_ID, DOC_APP_SECRET, FIXTURES_DIR, load_response

SUCCESS_WITHOUT_DATA = {"code": 200, "msg": "Success", "data": None}


@dataclass
class RecordedRequest:
    method: str
    endpoint: str
    query: dict[str, str]
    json_body: Any
    headers: dict[str, str]


@dataclass
class FakeResponse:
    body: Any = None
    status: int = 200
    raw_text: str | None = None
    delay_seconds: float = 0


@dataclass
class FakeAlphaEssCloud:
    """Local stand-in for openapi.alphaess.com that records every request.

    Endpoints answer with tests/fixtures/<endpoint>.json if present, else with
    a plain success; override per endpoint via ``responses``.
    """

    responses: dict[str, FakeResponse] = field(default_factory=dict)
    requests: list[RecordedRequest] = field(default_factory=list)

    def last_request(self) -> RecordedRequest:
        return self.requests[-1]

    def _response_for(self, endpoint: str) -> FakeResponse:
        if endpoint in self.responses:
            return self.responses[endpoint]
        if (FIXTURES_DIR / f"{endpoint}.json").exists():
            return FakeResponse(load_response(endpoint))
        return FakeResponse(SUCCESS_WITHOUT_DATA)

    async def handle(self, request: web.Request) -> web.Response:
        endpoint = request.match_info["endpoint"]
        self.requests.append(
            RecordedRequest(
                method=request.method,
                endpoint=endpoint,
                query=dict(request.query),
                json_body=await request.json() if request.can_read_body else None,
                headers=dict(request.headers),
            )
        )
        fake = self._response_for(endpoint)
        await asyncio.sleep(fake.delay_seconds)
        if fake.raw_text is not None:
            return web.Response(text=fake.raw_text, status=fake.status)
        return web.json_response(fake.body, status=fake.status)


@pytest.fixture
def auth() -> AlphaEssAuth:
    return AlphaEssAuth(appid=DOC_APP_ID, appsecret=DOC_APP_SECRET)


@pytest.fixture
def fake_cloud() -> FakeAlphaEssCloud:
    return FakeAlphaEssCloud()


@pytest.fixture
async def fake_cloud_url(aiohttp_server, fake_cloud: FakeAlphaEssCloud) -> str:
    app = web.Application()
    app.router.add_route("*", "/api/{endpoint}", fake_cloud.handle)
    server = await aiohttp_server(app)
    return str(server.make_url("/api/"))


@pytest.fixture
async def api(auth: AlphaEssAuth, fake_cloud_url: str):
    async with AlphaEssAPI(auth, base_url=fake_cloud_url, timeout=1) as client:
        yield client
