import json
import os
from typing import Any, cast

from ajera.client import AjeraClient

# =============================================================================
# CLASS: ClientContext
# =============================================================================


class ClientContext:
    """
    Lazy client holder attached to the Click context object.
    """

    def __init__(self, log: bool = False) -> None:
        self._log = log
        self._client: AjeraClient | None = None

    @property
    def client(self) -> AjeraClient:
        """
        Construct the underlying client on first access.

        Connection and credential settings are sourced from the standard
        `AJERA_API_*` environment variables. Extra request headers may be
        supplied as a JSON object in `AJERA_API_HEADERS` (e.g. to authenticate
        through a proxy that fronts the API).
        """
        if self._client is None:
            raw = os.environ.get("AJERA_API_HEADERS")
            headers: dict[str, str] = (
                cast(dict[str, Any], json.loads(raw)) if raw else {}
            )
            self._client = AjeraClient(log=self._log, headers=headers)
        return self._client
