import httpx
import pytest

from ajera.cli.context import ClientContext
from ajera.client import DEFAULT_TIMEOUT

# =============================================================================
# TEST: ClientContext.client headers
# =============================================================================


def test_client_reads_headers_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AJERA_API_HEADERS", '{"Authorization": "Bearer token123"}')

    client = ClientContext().client

    assert client.http.headers["Authorization"] == "Bearer token123"


def test_client_without_headers_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AJERA_API_HEADERS", raising=False)

    client = ClientContext().client

    assert "Authorization" not in client.http.headers


# =============================================================================
# TEST: ClientContext.client timeout / retries
# =============================================================================


def test_client_reads_timeout_and_retries_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AJERA_API_TIMEOUT", "45")
    monkeypatch.setenv("AJERA_API_RETRIES", "2")

    client = ClientContext().client

    assert client.timeout == 45.0
    transport = client.http._transport
    assert isinstance(transport, httpx.HTTPTransport)
    assert transport._pool._retries == 2


def test_client_without_timeout_env_uses_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AJERA_API_TIMEOUT", raising=False)
    monkeypatch.delenv("AJERA_API_RETRIES", raising=False)

    client = ClientContext().client

    assert client.timeout == DEFAULT_TIMEOUT
    assert client.http._transport._pool._retries == 0
