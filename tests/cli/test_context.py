import pytest

from ajera.cli.context import ClientContext

# =============================================================================
# TEST: ClientContext.client headers
# =============================================================================


def test_client_reads_headers_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AJERA_API_HEADERS", '{"Authorization": "Bearer token123"}')

    client = ClientContext().client

    assert client.session.headers["Authorization"] == "Bearer token123"


def test_client_without_headers_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AJERA_API_HEADERS", raising=False)

    client = ClientContext().client

    assert "Authorization" not in client.session.headers
