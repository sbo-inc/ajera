from typing import Any

import pytest
from urllib3.util.retry import Retry

from ajera.client import DEFAULT_TIMEOUT, AjeraClient
from ajera.schemas.session import CreateAPISession

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


def test_post_forwards_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AjeraClient(url="https://example.test/api", timeout=12.5)

    captured: dict[str, Any] = {}

    class FakeResponse:
        text = '{"ResponseCode": 200, "Content": {}}'

        def raise_for_status(self) -> None:
            pass

    def fake_post(**kwargs: Any) -> FakeResponse:
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr(client.session, "post", fake_post)

    client._post(CreateAPISession(username="u", password="p", api_version=1))

    assert captured["timeout"] == 12.5


# =============================================================================
# TEST: retry configuration
# =============================================================================


def test_no_retries_by_default() -> None:
    client = AjeraClient(url="https://example.test/api")
    # A default requests session mounts no urllib3 Retry object.
    adapter = client.session.get_adapter("https://example.test/api")
    assert not isinstance(adapter.max_retries, Retry) or adapter.max_retries.total == 0


def test_int_retries_only_connection_stage() -> None:
    client = AjeraClient(url="https://example.test/api", retries=3)

    for scheme in ("https://example.test/api", "http://example.test/api"):
        retry = client.session.get_adapter(scheme).max_retries
        assert isinstance(retry, Retry)
        assert retry.total == 3
        assert retry.connect == 3
        # Read-stage and method-based retries are disabled so a POST whose
        # response is lost is never resubmitted.
        assert retry.read == 0
        assert retry.allowed_methods == frozenset()


def test_retry_object_passed_through() -> None:
    custom = Retry(total=7, connect=7, read=2)
    client = AjeraClient(url="https://example.test/api", retries=custom)

    retry = client.session.get_adapter("https://example.test/api").max_retries
    assert retry is custom
