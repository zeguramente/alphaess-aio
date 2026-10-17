import aiohttp
import pytest

from alphaessaio import (
    AlphaEssAPI,
    AlphaEssAuthError,
    AlphaEssConnectionError,
    AlphaEssRequestError,
)
from tests.conftest import FakeResponse


async def test_request_returns_data_part_of_response(api, fake_cloud):
    fake_cloud.responses["getEssList"] = FakeResponse(
        {"code": 200, "msg": "Success", "data": [1]}
    )

    assert await api._request("GET", "getEssList") == [1]


async def test_request_sends_signed_headers(api, fake_cloud):
    await api._request("GET", "getEssList")

    headers = fake_cloud.last_request().headers
    assert {"appId", "timeStamp", "sign"} <= set(headers)


async def test_request_raises_auth_error_on_sign_verification_failure(api, fake_cloud):
    fake_cloud.responses["getEssList"] = FakeResponse(
        {"code": 6007, "msg": "Sign verification error"}
    )

    with pytest.raises(AlphaEssAuthError, match="Sign verification error") as exc_info:
        await api._request("GET", "getEssList")

    assert exc_info.value.code == 6007


@pytest.mark.parametrize(
    "fake_response",
    [
        FakeResponse({"code": 6002, "msg": "SN is not bound to the user"}),
        FakeResponse({"msg": "no code at all"}),
        FakeResponse({"code": 200, "msg": "Success", "data": None}, status=500),
        FakeResponse(["not", "a", "dict"]),
    ],
    ids=["api-error-code", "missing-code", "http-error", "unexpected-body"],
)
async def test_request_raises_request_error_on_unsuccessful_response(
    api, fake_cloud, fake_response
):
    fake_cloud.responses["getEssList"] = fake_response

    with pytest.raises(AlphaEssRequestError):
        await api._request("GET", "getEssList")


async def test_request_raises_request_error_on_invalid_json(api, fake_cloud):
    fake_cloud.responses["getEssList"] = FakeResponse(
        raw_text="<html>maintenance</html>", status=503
    )

    with pytest.raises(AlphaEssRequestError, match="invalid JSON"):
        await api._request("GET", "getEssList")


async def test_request_raises_connection_error_on_timeout(api, fake_cloud):
    fake_cloud.responses["getEssList"] = FakeResponse(
        {"code": 200, "data": None}, delay_seconds=2
    )

    with pytest.raises(AlphaEssConnectionError):
        await api._request("GET", "getEssList")


async def test_request_raises_connection_error_when_host_unreachable(auth):
    async with AlphaEssAPI(auth, base_url="http://127.0.0.1:1/api/") as api:
        with pytest.raises(AlphaEssConnectionError):
            await api._request("GET", "getEssList")


async def test_close_keeps_injected_session_open(auth):
    async with aiohttp.ClientSession() as shared_session:
        api = AlphaEssAPI(auth, session=shared_session)

        await api.close()

        assert not shared_session.closed


async def test_close_closes_own_session(auth, fake_cloud_url):
    api = AlphaEssAPI(auth, base_url=fake_cloud_url)
    await api._request("GET", "getEssList")
    own_session = api._session

    await api.close()

    assert own_session.closed
