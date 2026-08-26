import json
import logging
import os
from typing import Any

import httpx

from ajera.schemas.session import CreateAPISession

logger = logging.getLogger("ajera")
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("ajera: %(message)s"))
logger.addHandler(console_handler)

# Default (connect, read) timeout in seconds applied to every request. Without
# one, a stalled connection or an unresponsive server would block the caller
# far longer than any Ajera call legitimately takes.
DEFAULT_TIMEOUT: tuple[float, float] = (5.0, 30.0)

# ResponseCode values that do not by themselves mean the call failed.
# CreateAPISession answers 200 and every other method answers 0, so a code
# outside this pair is a failure and a code inside it settles nothing on its
# own. A failure carries entries in Errors, which is the signal that decides.
SUCCESS_CODES: tuple[int, ...] = (0, 200)


# =============================================================================
# CLASS: BaseAjeraClient
# =============================================================================


class BaseAjeraClient:
    """
    Transport-agnostic half of the Ajera clients.

    Holds everything that does not depend on whether the underlying HTTP call
    is awaited: configuration and its environment fallbacks, the per-version
    session-token cache, the login request, and the response-envelope check.
    `AjeraClient` and `AsyncAjeraClient` add only the transport.
    """

    url: str | None
    username: str | None
    password: str | None
    timeout: float | tuple[float, float] | None

    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        log: bool = False,
        timeout: float | tuple[float, float] | None = DEFAULT_TIMEOUT,
    ) -> None:
        """
        Resolve configuration, falling back to the `AJERA_API_*` environment.

        Args:
            url: The base URL of the API (Environment: `AJERA_API_URL`)
            username: The username to authenticate with (Environment: `AJERA_API_USERNAME`)
            password: The password to authenticate with (Environment: `AJERA_API_PASSWORD`)
            log: Enables request logging at INFO level
            timeout: Per-request timeout in seconds applied to every call.
        """
        if log:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.CRITICAL)

        self.url = url or os.environ.get("AJERA_API_URL")
        self.username = username or os.environ.get("AJERA_API_USERNAME")
        self.password = password or os.environ.get("AJERA_API_PASSWORD")
        self.timeout = timeout

        self._session_tokens: dict[int, str] = {}

    # -------------------------------------------------------------------------
    # METHOD: _require_url
    # -------------------------------------------------------------------------

    def _require_url(self) -> str:
        """
        Return the configured API URL, raising if it was never set.

        Returns:
            str: The base URL of the API.
        """
        if not self.url:
            raise ValueError("No URL provided")
        return self.url

    # -------------------------------------------------------------------------
    # METHOD: _login_request
    # -------------------------------------------------------------------------

    def _login_request(self, api_version: int) -> CreateAPISession:
        """
        Build the CreateAPISession request, raising if credentials are missing.

        Credentials are validated here rather than at construction so that a
        caller who injects a token into `_session_tokens`, or who authenticates
        through a proxy, never has to supply them.

        Returns:
            CreateAPISession: The login request for the given API version.
        """
        username = self.username
        password = self.password
        if not username or not password:
            raise ValueError("No username or password provided")

        return CreateAPISession(
            username=username,
            password=password,
            api_version=api_version,
        )

    # -------------------------------------------------------------------------
    # METHOD: _request_timeout
    # -------------------------------------------------------------------------

    def _request_timeout(self) -> httpx.Timeout | None:
        """
        Translate the configured timeout into the httpx representation.

        A `(connect, read)` pair carries over from the `requests` convention;
        the write and pool stages inherit the read and connect budgets
        respectively, since neither has a meaningful budget of its own here.

        Returns:
            httpx.Timeout | None: The per-request timeout, or None to disable.
        """
        timeout = self.timeout
        if timeout is None:
            return None
        if isinstance(timeout, tuple):
            connect, read = timeout
            return httpx.Timeout(connect=connect, read=read, write=read, pool=connect)
        return httpx.Timeout(timeout)

    # -------------------------------------------------------------------------
    # METHOD: _decode
    # -------------------------------------------------------------------------

    def _decode(self, response: httpx.Response) -> dict[str, Any]:
        """
        Raise on a transport or API-level failure, and decode the envelope.

        Every Ajera response is the same envelope, and a failed call still
        arrives as HTTP 200, so the status check alone would let errors
        through. `Errors` is what separates the two cases: `ResponseCode` is
        `200` for `CreateAPISession` and `0` for every other method, and `0`
        also accompanies a failure, so the code alone decides nothing.

        Returns:
            dict[str, Any]: The decoded JSON response body.
        """
        response.raise_for_status()
        data: dict[str, Any] = json.loads(response.text)

        code = data.get("ResponseCode", "No code")
        errors: list = data.get("Errors") or []
        if errors or ("ResponseCode" in data and code not in SUCCESS_CODES):
            message = data.get("Message", "No message")
            raise Exception(
                f"API Error (Response Code: {code})\nMessage: {message}\nErrors: {errors}"
            )

        return data
