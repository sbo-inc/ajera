"""
Shared helpers for the unit tests.

Both clients are driven through `httpx.MockTransport`, so one handler function
can stand in for the API on either surface and the sync and async paths are
asserted against the same fixture data.
"""

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from ajera.async_client import AsyncAjeraClient
from ajera.client import AjeraClient

URL = "https://example.test/api"

Handler = Callable[[httpx.Request], httpx.Response]


# =============================================================================
# FUNCTIONS: Envelope helpers
# =============================================================================


def body(request: httpx.Request) -> dict[str, Any]:
    """
    Decode the JSON body a client sent.

    Returns:
        dict[str, Any]: The decoded request body.
    """
    return json.loads(request.content)


def envelope(content: Any = None, **extra: Any) -> httpx.Response:
    """
    Build an HTTP 200 carrying a successful Ajera envelope.

    Returns:
        httpx.Response: The mocked response.
    """
    payload: dict[str, Any] = {
        "ResponseCode": 200,
        "Content": {} if content is None else content,
        **extra,
    }
    return httpx.Response(200, json=payload)


def error_envelope(message: str = "Boom", code: int = -100) -> httpx.Response:
    """
    Build an HTTP 200 carrying a failed Ajera envelope.

    A failed Ajera call still arrives as HTTP 200, which is why the clients
    check `ResponseCode` rather than the status alone.

    Returns:
        httpx.Response: The mocked response.
    """
    return httpx.Response(
        200,
        json={"ResponseCode": code, "Message": message, "Errors": ["detail"]},
    )


def session_envelope(token: str = "token") -> httpx.Response:
    """
    Build the CreateAPISession response.

    Returns:
        httpx.Response: The mocked login response.
    """
    return envelope({"SessionToken": token})


def with_login(handler: Handler, token: str = "token") -> Handler:
    """
    Wrap a handler so CreateAPISession is answered before it is reached.

    Returns:
        Handler: The wrapped handler.
    """

    def route(request: httpx.Request) -> httpx.Response:
        if body(request)["Method"] == "CreateAPISession":
            return session_envelope(token)
        return handler(request)

    return route


# =============================================================================
# FIXTURES: Environment isolation
# =============================================================================


AJERA_ENV_VARS = (
    "AJERA_API_URL",
    "AJERA_API_USERNAME",
    "AJERA_API_PASSWORD",
    "AJERA_API_HEADERS",
    "AJERA_API_TIMEOUT",
    "AJERA_API_RETRIES",
)


@pytest.fixture(autouse=True)
def isolate_environment(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Clear the `AJERA_API_*` variables so unit tests never read the real shell.

    Without this a developer with credentials exported sees different
    behaviour from CI, which has none: config falls back to the environment,
    so whether a call fails on the missing URL or the missing credentials
    depends on who is running the suite. Integration tests are exempt - the
    live environment is the point.
    """
    if request.node.get_closest_marker("integration"):
        return

    for name in AJERA_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


# =============================================================================
# FIXTURES: Mock-transport clients
# =============================================================================


@pytest.fixture
def make_client() -> Callable[..., AjeraClient]:
    """
    Return a factory building an `AjeraClient` backed by a handler.

    Returns:
        Callable[..., AjeraClient]: The client factory.
    """

    def factory(handler: Handler, *, login: bool = True, **kwargs: Any) -> AjeraClient:
        client = AjeraClient(url=URL, username="u", password="p", **kwargs)
        headers = client.http.headers
        client.close()
        client._http = httpx.Client(
            headers=headers,
            transport=httpx.MockTransport(with_login(handler) if login else handler),
        )
        return client

    return factory


@pytest.fixture
def make_async_client() -> Callable[..., AsyncAjeraClient]:
    """
    Return a factory building an `AsyncAjeraClient` backed by a handler.

    Returns:
        Callable[..., AsyncAjeraClient]: The client factory.
    """

    def factory(
        handler: Handler, *, login: bool = True, **kwargs: Any
    ) -> AsyncAjeraClient:
        client = AsyncAjeraClient(url=URL, username="u", password="p", **kwargs)
        headers = client.http.headers
        client._http = httpx.AsyncClient(
            headers=headers,
            transport=httpx.MockTransport(with_login(handler) if login else handler),
        )
        return client

    return factory
