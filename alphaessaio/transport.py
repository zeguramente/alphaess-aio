"""HTTP transport: session handling, signing and response checking."""

import asyncio
import json
import logging
from http import HTTPStatus
from typing import Any, Literal

import aiohttp

from alphaessaio.auth import AlphaEssAuth
from alphaessaio.exceptions import (
    AlphaEssAuthError,
    AlphaEssConnectionError,
    AlphaEssRequestError,
)

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://openapi.alphaess.com/api/"
_SUCCESS_CODE = 200
_SIGN_VERIFICATION_FAILED_CODE = 6007


class AlphaEssTransport:
    """Send signed requests to the AlphaESS Open API.

    Args:
        auth: Developer credentials used to sign every request.
        session: Shared aiohttp session, e.g. Home Assistant's
            ``async_get_clientsession(hass)``. If omitted, an own session is
            created on first use and closed by ``close()``.
        timeout: Total timeout per request in seconds.
        base_url: API root, only to be changed for tests or proxies.
    """

    def __init__(
        self,
        auth: AlphaEssAuth,
        session: aiohttp.ClientSession | None = None,
        *,
        timeout: float = 30,
        base_url: str = BASE_URL,
    ) -> None:
        self.auth = auth
        self._base_url = base_url
        self._session = session
        self._owns_session = session is None
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the session if it was created by this client."""
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def _request(
        self,
        method: Literal["GET", "POST"],
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Send a signed request and return the ``data`` part of the response.

        GET parameters are sent as query string, POST parameters as JSON body.

        Raises:
            AlphaEssConnectionError: On network errors or timeouts.
            AlphaEssAuthError: If the signature was rejected.
            AlphaEssRequestError: If the API returned an error code or no JSON.
        """
        url = f"{self._base_url}{endpoint}"
        payload_key = "params" if method == "GET" else "json"
        _LOGGER.debug("%s %s %s", method, url, params)
        try:
            async with self._get_session().request(
                method,
                url,
                headers=self.auth.create_headers(),
                timeout=self._timeout,
                **{payload_key: params or {}},
            ) as response:
                http_status = response.status
                body = await response.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise AlphaEssConnectionError(f"{method} {url} failed: {err!r}") from err
        except json.JSONDecodeError as err:
            raise AlphaEssRequestError(
                f"{endpoint} returned invalid JSON (HTTP {http_status})"
            ) from err

        return _extract_data(endpoint, http_status, body)


def _extract_data(endpoint: str, http_status: int, body: Any) -> Any:
    _LOGGER.debug("%s answered %s: %s", endpoint, http_status, body)
    if not isinstance(body, dict):
        raise AlphaEssRequestError(f"{endpoint} returned unexpected body {body!r}")

    code = body.get("code")
    message = body.get("msg") or body.get("info") or ""
    if http_status == HTTPStatus.OK and code == _SUCCESS_CODE:
        return body.get("data")
    if code == _SIGN_VERIFICATION_FAILED_CODE:
        raise AlphaEssAuthError(
            f"Authentication failed, check AppID and AppSecret: {message}", code
        )
    raise AlphaEssRequestError(
        f"{endpoint} failed (HTTP {http_status}): {message}", code
    )
