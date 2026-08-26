from collections.abc import Callable
from typing import Any

import httpx
import pytest
from conftest import body, envelope, error_envelope, session_envelope, with_login

from ajera.client import DEFAULT_TIMEOUT, AjeraClient

# =============================================================================
# TEST: timeout configuration
# =============================================================================


def test_default_timeout() -> None:
    client = AjeraClient(url="https://example.test/api")
    assert client.timeout == DEFAULT_TIMEOUT


def test_custom_timeout() -> None:
    client = AjeraClient(url="https://example.test/api", timeout=(1.0, 2.0))
    assert client.timeout == (1.0, 2.0)


def test_timeout_none_disables() -> None:
    client = AjeraClient(url="https://example.test/api", timeout=None)
    assert client.timeout is None


def test_timeout_tuple_maps_onto_the_httpx_stages() -> None:
    client = AjeraClient(url="https://example.test/api", timeout=(1.0, 2.0))

    # The (connect, read) pair carries over from the requests convention; write
    # inherits the read budget and pool the connect budget.
    assert client._request_timeout() == httpx.Timeout(
        connect=1.0, read=2.0, write=2.0, pool=1.0
    )


def test_post_forwards_a_scalar_timeout(
    make_client: Callable[..., AjeraClient],
) -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(request.extensions["timeout"])
        return envelope()

    client = make_client(handler, timeout=12.5, login=False)
    client.get_session_info()

    assert captured == {
        "connect": 12.5,
        "read": 12.5,
        "write": 12.5,
        "pool": 12.5,
    }


def test_post_forwards_the_default_tuple_timeout(
    make_client: Callable[..., AjeraClient],
) -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(request.extensions["timeout"])
        return envelope()

    client = make_client(handler, login=False)
    client.get_session_info()

    assert captured == {"connect": 5.0, "read": 30.0, "write": 30.0, "pool": 5.0}


def test_post_disables_the_timeout_when_none(
    make_client: Callable[..., AjeraClient],
) -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(request.extensions["timeout"])
        return envelope()

    client = make_client(handler, timeout=None, login=False)
    client.get_session_info()

    assert set(captured.values()) == {None}


# =============================================================================
# TEST: retry configuration
# =============================================================================


def test_no_retries_by_default() -> None:
    client = AjeraClient(url="https://example.test/api")

    assert client.http._transport._pool._retries == 0


def test_int_retries_only_the_connection_stage() -> None:
    client = AjeraClient(url="https://example.test/api", retries=3)

    transport = client.http._transport
    assert isinstance(transport, httpx.HTTPTransport)
    # httpx retries connection establishment only, so a POST whose response is
    # lost is never resubmitted.
    assert transport._pool._retries == 3


# =============================================================================
# TEST: headers
# =============================================================================


def test_content_type_is_set_by_default() -> None:
    client = AjeraClient(url="https://example.test/api")

    assert client.http.headers["Content-Type"] == "application/json"


def test_extra_headers_ride_along_with_every_request(
    make_client: Callable[..., AjeraClient],
) -> None:
    seen: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("Authorization"))
        return envelope()

    client = make_client(
        handler, headers={"Authorization": "Bearer token123"}, login=False
    )
    client.get_session_info()

    # Login posts through the same client, so a credential-injecting proxy sees
    # the header on the login call too.
    assert seen == ["Bearer token123"]


def test_session_is_an_alias_for_http() -> None:
    client = AjeraClient(url="https://example.test/api")

    assert client.session is client.http


# =============================================================================
# TEST: the response envelope
# =============================================================================


def test_a_reported_error_raises(
    make_client: Callable[..., AjeraClient],
) -> None:
    client = make_client(lambda request: error_envelope("Nope"), login=False)

    with pytest.raises(Exception, match="Nope"):
        client.get_session_info()


def test_a_zero_response_code_carrying_errors_raises(
    make_client: Callable[..., AjeraClient],
) -> None:
    client = make_client(
        lambda request: error_envelope("Bad args", code=0), login=False
    )

    with pytest.raises(Exception, match="Bad args"):
        client.get_session_info()


def test_a_zero_response_code_without_errors_is_a_success(
    make_client: Callable[..., AjeraClient],
) -> None:
    # Every method except CreateAPISession answers 0 on success, so reading
    # the code alone would fail every List call against a live tenant.
    client = make_client(with_login(lambda request: envelope({"Departments": []})))

    assert client.list_departments() == []


def test_http_error_raises(make_client: Callable[..., AjeraClient]) -> None:
    client = make_client(lambda request: httpx.Response(500), login=False)

    with pytest.raises(httpx.HTTPStatusError):
        client.get_session_info()


# =============================================================================
# TEST: session tokens
# =============================================================================


def test_token_is_minted_once_and_reused(
    make_client: Callable[..., AjeraClient],
) -> None:
    methods: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        method = body(request)["Method"]
        methods.append(method)
        if method == "CreateAPISession":
            return session_envelope()
        return envelope({"Companies": []})

    client = make_client(handler, login=False)
    client.list_companies()
    client.list_companies()

    assert methods == ["CreateAPISession", "ListCompanies", "ListCompanies"]


def test_each_api_version_mints_its_own_token(
    make_client: Callable[..., AjeraClient],
) -> None:
    versions: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = body(request)
        if payload["Method"] == "CreateAPISession":
            versions.append(payload["APIVersion"])
            return session_envelope()
        return envelope({"Companies": [], "Projects": []})

    client = make_client(handler, login=False)
    client.list_companies()  # v1
    client.list_projects()  # v2

    assert versions == [1, 2]


def test_an_injected_token_needs_no_credentials(
    make_client: Callable[..., AjeraClient],
) -> None:
    tokens: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        tokens.append(body(request)["SessionToken"])
        return envelope({"Companies": []})

    client = make_client(handler, login=False)
    client.username = None
    client.password = None
    client._session_tokens[1] = "injected"

    client.list_companies()

    assert tokens == ["injected"]


# =============================================================================
# TEST: lifecycle
# =============================================================================


def test_close_closes_the_underlying_client() -> None:
    client = AjeraClient(url="https://example.test/api")
    client.close()

    assert client.http.is_closed


def test_context_manager_closes_on_exit() -> None:
    with AjeraClient(url="https://example.test/api") as client:
        assert not client.http.is_closed

    assert client.http.is_closed


def test_url_is_required_before_any_post() -> None:
    # Credentials resolve, so the missing URL is the only thing left to fail on.
    client = AjeraClient(url=None, username="u", password="p")

    with pytest.raises(ValueError, match="No URL provided"):
        client.get_session_info()


def test_credentials_are_required_to_mint_a_token() -> None:
    client = AjeraClient(url="https://example.test/api")

    with pytest.raises(ValueError, match="No username or password provided"):
        client.get_session_info()
