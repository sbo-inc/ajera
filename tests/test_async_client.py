import asyncio
import inspect
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from conftest import body, envelope, error_envelope, session_envelope

from ajera.async_client import AsyncAjeraClient
from ajera.client import DEFAULT_TIMEOUT, AjeraClient

# =============================================================================
# TEST: parity with the sync client
# =============================================================================
#
# The two clients are meant to be the same surface with a different transport,
# so the check is mechanical: every public method exists on both, the async one
# is a coroutine function, and the signatures and docstrings match exactly.


def _public_methods(cls: type) -> set[str]:
    return {
        name
        for name, value in vars(cls).items()
        if not name.startswith("_") and inspect.isfunction(value)
    }


SYNC_ONLY = {"close", "session"}
ASYNC_ONLY = {"aclose"}


def test_every_sync_method_has_an_async_twin() -> None:
    assert _public_methods(AjeraClient) - SYNC_ONLY == (
        _public_methods(AsyncAjeraClient) - ASYNC_ONLY
    )


@pytest.mark.parametrize("name", sorted(_public_methods(AjeraClient) - SYNC_ONLY))
def test_async_methods_match_their_sync_twin(name: str) -> None:
    sync = getattr(AjeraClient, name)
    asynchronous = getattr(AsyncAjeraClient, name)

    assert inspect.iscoroutinefunction(asynchronous)
    assert inspect.signature(sync) == inspect.signature(asynchronous)
    assert sync.__doc__ == asynchronous.__doc__


# =============================================================================
# TEST: configuration
# =============================================================================


def test_reads_configuration_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AJERA_API_URL", "https://env.test/api")
    monkeypatch.setenv("AJERA_API_USERNAME", "env-user")
    monkeypatch.setenv("AJERA_API_PASSWORD", "env-password")

    client = AsyncAjeraClient()

    assert client.url == "https://env.test/api"
    assert client.username == "env-user"
    assert client.password == "env-password"
    assert client.timeout == DEFAULT_TIMEOUT


def test_no_retries_by_default() -> None:
    client = AsyncAjeraClient(url="https://example.test/api")

    assert client.http._transport._pool._retries == 0


def test_int_retries_only_the_connection_stage() -> None:
    client = AsyncAjeraClient(url="https://example.test/api", retries=3)

    transport = client.http._transport
    assert isinstance(transport, httpx.AsyncHTTPTransport)
    assert transport._pool._retries == 3


def test_content_type_is_set_by_default() -> None:
    client = AsyncAjeraClient(url="https://example.test/api")

    assert client.http.headers["Content-Type"] == "application/json"


async def test_extra_headers_ride_along_with_every_request(
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    seen: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("Authorization"))
        return envelope()

    client = make_async_client(
        handler, headers={"Authorization": "Bearer token123"}, login=False
    )
    await client.get_session_info()

    assert seen == ["Bearer token123"]


async def test_post_forwards_the_timeout(
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(request.extensions["timeout"])
        return envelope()

    client = make_async_client(handler, timeout=(1.0, 2.0), login=False)
    await client.get_session_info()

    assert captured == {"connect": 1.0, "read": 2.0, "write": 2.0, "pool": 1.0}


# =============================================================================
# TEST: the response envelope
# =============================================================================


async def test_non_200_response_code_raises(
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    client = make_async_client(lambda request: error_envelope("Nope"), login=False)

    with pytest.raises(Exception, match="Nope"):
        await client.get_session_info()


async def test_http_error_raises(
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    client = make_async_client(lambda request: httpx.Response(500), login=False)

    with pytest.raises(httpx.HTTPStatusError):
        await client.get_session_info()


# =============================================================================
# TEST: session tokens
# =============================================================================


async def test_gathered_calls_mint_exactly_one_token(
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    """
    The motivating case: N tasks against a cold cache log in once, not N times.
    """
    methods: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        method = body(request)["Method"]
        methods.append(method)
        # Yield so the gathered tasks interleave inside the login, which is
        # exactly the window the lock exists to close.
        await asyncio.sleep(0)
        if method == "CreateAPISession":
            return session_envelope()
        return envelope({"ProjectTotals": {"ProjectKey": 1}})

    client = make_async_client(handler, login=False)

    await asyncio.gather(*(client.get_project_totals(key) for key in range(10)))

    assert methods.count("CreateAPISession") == 1
    assert methods.count("GetProjectTotals") == 10


async def test_each_api_version_mints_its_own_token(
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    versions: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = body(request)
        if payload["Method"] == "CreateAPISession":
            versions.append(payload["APIVersion"])
            return session_envelope()
        return envelope({"Companies": [], "Projects": []})

    client = make_async_client(handler, login=False)
    await client.list_companies()  # v1
    await client.list_projects()  # v2

    assert versions == [1, 2]


async def test_an_injected_token_needs_no_credentials(
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    tokens: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        tokens.append(body(request)["SessionToken"])
        return envelope({"Companies": []})

    client = make_async_client(handler, login=False)
    client.username = None
    client.password = None
    client._session_tokens[1] = "injected"

    await client.list_companies()

    assert tokens == ["injected"]


# =============================================================================
# TEST: results match the sync client
# =============================================================================


async def test_both_clients_parse_the_same_response(
    make_client: Callable[..., AjeraClient],
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return envelope(
            {
                "Companies": [
                    {"CompanyKey": 2, "Description": "Beta"},
                    {"CompanyKey": 1, "Description": "Alpha"},
                ]
            }
        )

    synchronous = make_client(handler).list_companies()
    asynchronous = await make_async_client(handler).list_companies()

    assert synchronous == asynchronous
    # List responses sort themselves, and that reshaping is shared code.
    assert [company.description for company in asynchronous] == ["Alpha", "Beta"]


async def test_bodies_are_identical_on_both_clients(
    make_client: Callable[..., AjeraClient],
    make_async_client: Callable[..., AsyncAjeraClient],
) -> None:
    sent: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(body(request))
        return envelope({"Employees": []})

    make_client(handler).list_employees(filter_by_company=[1])
    await make_async_client(handler).list_employees(filter_by_company=[1])

    assert sent[0] == sent[1]


# =============================================================================
# TEST: lifecycle
# =============================================================================


async def test_aclose_closes_the_underlying_client() -> None:
    client = AsyncAjeraClient(url="https://example.test/api")
    await client.aclose()

    assert client.http.is_closed


async def test_context_manager_closes_on_exit() -> None:
    async with AsyncAjeraClient(url="https://example.test/api") as client:
        assert not client.http.is_closed

    assert client.http.is_closed


async def test_url_is_required_before_any_post() -> None:
    # Credentials resolve, so the missing URL is the only thing left to fail on.
    client = AsyncAjeraClient(url=None, username="u", password="p")

    with pytest.raises(ValueError, match="No URL provided"):
        await client.get_session_info()


async def test_credentials_are_required_to_mint_a_token() -> None:
    client = AsyncAjeraClient(url="https://example.test/api")

    with pytest.raises(ValueError, match="No username or password provided"):
        await client.get_session_info()
