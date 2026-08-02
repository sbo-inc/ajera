"""
Live read-only coverage of the client surface.

Every call here is a `List*` or `Get*`; nothing in this module writes. The
sweep is the regression net for the transport refactor: each read is driven
through both `AjeraClient` and `AsyncAjeraClient` and the two results are
compared, so a divergence between the surfaces fails the suite.
"""

import asyncio
import os
from collections.abc import AsyncGenerator, Callable
from typing import Any

import pytest
import pytest_asyncio

from ajera.async_client import AsyncAjeraClient
from ajera.client import AjeraClient
from ajera.schemas.employee import Employee

# One client is shared across the module, the way a consumer shares it across
# tasks, so its connection pool and session token are reused. That requires one
# event loop for the whole module: a pooled connection belongs to the loop it
# was opened in.
pytestmark: list[pytest.MarkDecorator] = [
    pytest.mark.integration,
    pytest.mark.asyncio(loop_scope="module"),
]

REQUIRED_ENV_VARS = ("AJERA_API_URL", "AJERA_API_USERNAME", "AJERA_API_PASSWORD")

# The API throttles at roughly 9 requests per second, so gathered calls are
# bounded well below it.
CONCURRENCY = 4


@pytest.fixture(scope="module")
def client() -> AjeraClient:
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        raise RuntimeError(
            "Ajera integration test misconfigured; set environment variables: "
            + ", ".join(missing)
        )
    return AjeraClient()


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def async_client() -> AsyncGenerator[AsyncAjeraClient]:
    async with AsyncAjeraClient() as client:
        yield client


@pytest.fixture(scope="module")
def keys(client: AjeraClient) -> dict[str, Any]:
    """
    Resolve one real key per entity, so the `Get*` reads have something to ask for.

    Returns:
        dict[str, Any]: The first key found for each entity, or None.
    """

    def first(records: list[Any], attribute: str) -> Any:
        return getattr(records[0], attribute) if records else None

    project_key = first(client.list_projects(), "project_key")

    return {
        "employee": first(client.list_employees(), "employee_key"),
        "client": first(client.list_clients(), "client_key"),
        "contact": first(client.list_contacts(), "contact_key"),
        "vendor": first(client.list_vendors(), "vendor_key"),
        "vendor_invoice": first(client.list_vendor_invoices(), "vendor_invoice_key"),
        "project": project_key,
        "project_template": first(
            client.list_project_templates(), "project_template_key"
        ),
        "ledger_account": first(client.list_ledger_accounts(), "account_key"),
    }


# =============================================================================
# TEST: session
# =============================================================================


async def test_get_session_token(
    client: AjeraClient, async_client: AsyncAjeraClient
) -> None:
    for token in (
        client.get_session_token(api_version=1),
        await async_client.get_session_token(api_version=1),
    ):
        assert isinstance(token, str)
        assert token


async def test_list_employees(
    client: AjeraClient, async_client: AsyncAjeraClient
) -> None:
    for employees in (client.list_employees(), await async_client.list_employees()):
        assert isinstance(employees, list)
        assert all(isinstance(employee, Employee) for employee in employees)


async def test_session_info_matches_on_both_clients(
    client: AjeraClient, async_client: AsyncAjeraClient
) -> None:
    # Each login mints its own token; everything else about the session is the
    # same company, version, and calling identity.
    asynchronous = await async_client.get_session_info()
    synchronous = client.get_session_info()

    volatile = {"session_token", "session_expiration"}

    assert asynchronous.session_token != synchronous.session_token
    assert asynchronous.model_dump(exclude=volatile) == synchronous.model_dump(
        exclude=volatile
    )


# =============================================================================
# TEST: the read surface
# =============================================================================
#
# Each entry names a client method and builds its arguments from the resolved
# keys. Returning None marks the read as unavailable on this tenant (no such
# record exists), which skips it rather than failing.

Arguments = tuple[tuple[Any, ...], dict[str, Any]]
Builder = Callable[[dict[str, Any]], Arguments | None]

NO_ARGS: Arguments = ((), {})


def _by_key(name: str, *, plural: bool = True) -> Builder:
    def build(keys: dict[str, Any]) -> Arguments | None:
        key = keys[name]
        if key is None:
            return None
        return (([key],) if plural else (key,), {})

    return build


READS: list[tuple[str, Builder]] = [
    # Employees
    ("list_employees", lambda keys: NO_ARGS),
    ("get_employees", _by_key("employee")),
    ("list_employee_types", lambda keys: NO_ARGS),
    ("list_deductions", lambda keys: NO_ARGS),
    ("list_fringes", lambda keys: NO_ARGS),
    # Clients
    ("list_clients", lambda keys: NO_ARGS),
    ("get_clients", _by_key("client")),
    ("list_client_types", lambda keys: NO_ARGS),
    # Contacts
    ("list_contacts", lambda keys: NO_ARGS),
    ("get_contacts", _by_key("contact")),
    ("list_contact_types", lambda keys: NO_ARGS),
    # Vendors
    ("list_vendors", lambda keys: NO_ARGS),
    ("get_vendors", _by_key("vendor")),
    ("list_vendor_types", lambda keys: NO_ARGS),
    # Vendor invoices
    ("list_vendor_invoices", lambda keys: NO_ARGS),
    ("list_vendor_invoices", lambda keys: ((), {"with_payment_status": True})),
    ("get_vendor_invoices", _by_key("vendor_invoice")),
    # Projects
    ("list_projects", lambda keys: NO_ARGS),
    ("get_projects", _by_key("project")),
    ("get_project_totals", _by_key("project", plural=False)),
    ("get_project_summary", _by_key("project", plural=False)),
    ("list_project_types", lambda keys: NO_ARGS),
    ("list_project_templates", lambda keys: NO_ARGS),
    ("get_project_templates", _by_key("project_template")),
    ("list_chargeable_phases", _by_key("project", plural=False)),
    # Ledger
    ("list_ledger_accounts", lambda keys: NO_ARGS),
    ("get_ledger_accounts", _by_key("ledger_account")),
    ("list_account_groups", lambda keys: NO_ARGS),
    # Reference lists
    ("list_activities", lambda keys: NO_ARGS),
    ("list_bank_accounts", lambda keys: NO_ARGS),
    ("list_companies", lambda keys: NO_ARGS),
    ("list_departments", lambda keys: NO_ARGS),
    ("list_invoice_formats", lambda keys: NO_ARGS),
    ("list_payroll_taxes", lambda keys: NO_ARGS),
    ("list_pays", lambda keys: NO_ARGS),
    ("list_rate_tables", lambda keys: NO_ARGS),
    ("list_wage_tables", lambda keys: NO_ARGS),
]


@pytest.mark.parametrize(
    "name, builder",
    READS,
    ids=[f"{index}-{name}" for index, (name, _) in enumerate(READS)],
)
async def test_read_agrees_across_both_clients(
    client: AjeraClient,
    async_client: AsyncAjeraClient,
    keys: dict[str, Any],
    name: str,
    builder: Builder,
) -> None:
    arguments = builder(keys)
    if arguments is None:
        pytest.skip(f"no record available for {name}")
    args, kwargs = arguments

    expected = getattr(client, name)(*args, **kwargs)
    actual = await getattr(async_client, name)(*args, **kwargs)

    assert actual == expected


# =============================================================================
# TEST: the motivating case
# =============================================================================


async def test_gathered_reads_share_one_session(
    client: AjeraClient, keys: dict[str, Any]
) -> None:
    """
    Fan out over a real tenant the way a consumer would, under a semaphore.
    """
    if keys["project"] is None:
        pytest.skip("no projects available")

    project_keys = [project.project_key for project in client.list_projects()][:10]
    limit = asyncio.Semaphore(CONCURRENCY)

    # A fresh client, so the token cache starts cold and the gathered tasks
    # race for it exactly as they would on a consumer's first request.
    async with AsyncAjeraClient() as async_client:

        async def totals(project_key: int) -> Any:
            async with limit:
                return await async_client.get_project_totals(project_key)

        results = await asyncio.gather(*(totals(key) for key in project_keys))
        minted = dict(async_client._session_tokens)

    assert len(results) == len(project_keys)
    # One login, however many tasks asked for a token.
    assert list(minted) == [1]
    assert results == [client.get_project_totals(key) for key in project_keys]
