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
        `AJERA_API_*` environment variables.
        """
        if self._client is None:
            self._client = AjeraClient(log=self._log)
        return self._client
