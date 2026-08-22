[![CI](https://github.com/sbo-inc/ajera/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/sbo-inc/ajera/actions/workflows/ci.yaml)
[![PyPI](https://img.shields.io/pypi/v/ajera.svg)](https://pypi.org/project/ajera/)
[![Python versions](https://img.shields.io/pypi/pyversions/ajera.svg)](https://pypi.org/project/ajera/)
[![License](https://img.shields.io/pypi/l/ajera.svg)](https://github.com/sbo-inc/ajera/blob/main/LICENSE)

# Deltek Ajera Python client

An unofficial typed Python client and command-line interface for the [Deltek Ajera](https://www.deltek.com/en/project-based-erp/ajera) API - no affiliation with Deltek is implied or intended.

Ajera exposes a single JSON-RPC style endpoint; this package wraps it in an ergonomic, fully type-hinted client built on [Pydantic](https://docs.pydantic.dev/) models, plus an `ajera` CLI for quick access from the terminal. Responses are validated and normalized into predictable Python objects so you can work with employees, projects, vendors, invoices, and general-ledger data without hand-rolling request payloads.

## Features

- **Typed models** - every response is parsed into Pydantic models with descriptive fields.
- **Python client and CLI** - use it as a library or straight from the shell via `ajera`.
- **Sync and async** - `AjeraClient` and `AsyncAjeraClient` expose the same methods over `httpx`.
- **Sensible defaults** - handles session tokens and per-method API versions for you.
- **Read and write** - list, get, update, and create across the supported APIs.

## Installation

The package is published on PyPI as [`ajera`](https://pypi.org/project/ajera/):

```bash
pip install ajera
# or, with uv:
uv add ajera
```

Requires Python 3.12+.

## Configuration

Credentials are read from environment variables (or can be passed directly to `AjeraClient`):

| Variable | Description |
| --- | --- |
| `AJERA_API_URL` | The Ajera API endpoint URL for your tenant. |
| `AJERA_API_USERNAME` | API username. |
| `AJERA_API_PASSWORD` | API password. |

```bash
export AJERA_API_URL="https://ajera.com/V0000000/AjeraAPI.ashx?..."
export AJERA_API_USERNAME="your-username"
export AJERA_API_PASSWORD="your-password"
```

For setting up an API user and generating credentials, see the [Deltek Ajera Learning Hub API docs](https://learning.deltek.com/bundle/ajera/page/Content/api_setting_up_api_user.htm).

### Timeouts and retries

Every request carries a timeout (default `(5, 30)` seconds for connect and read) so a stalled connection can't hang the caller forever. Pass `timeout=` to override it (a single float, a `(connect, read)` tuple, or `None` to disable), and `retries=` to retry connection-establishment failures:

```python
# Wait longer, and retry a dropped/stale connection up to 3 times.
client = AjeraClient(timeout=60, retries=3)
```

`retries` retries only the connection stage (before any bytes reach the server), which is safe for the non-idempotent writes this client performs: a create whose response is merely lost is never resubmitted. The CLI reads `AJERA_API_TIMEOUT` (seconds) and `AJERA_API_RETRIES` (count) for the same behavior.

## Quick start

### Python

```python
from ajera import AjeraClient

# Reads AJERA_API_URL / AJERA_API_USERNAME / AJERA_API_PASSWORD from the
# environment, or pass url=, username=, password= explicitly.
client = AjeraClient()

for employee in client.list_employees():
    print(employee.employee_key, employee.first_name, employee.last_name)
```

### Python (async)

`AsyncAjeraClient` mirrors `AjeraClient` method for method - same arguments, same return types, awaited. Share one instance across tasks so they reuse its connection pool and session token, and bound the fan-out with a semaphore (the API throttles at roughly 9 requests per second):

```python
import asyncio

from ajera import AsyncAjeraClient


async def main() -> None:
    async with AsyncAjeraClient() as client:
        projects = await client.list_projects()
        limit = asyncio.Semaphore(5)

        async def totals(project_key: int):
            async with limit:
                return await client.get_project_totals(project_key)

        for total in await asyncio.gather(
            *(totals(project.project_key) for project in projects)
        ):
            print(total.project_key, total.totals)


asyncio.run(main())
```

Outside a context manager, call `await client.aclose()` when you're done with it.

### CLI

```console
$ ajera employees list
[
  {
    "employee_key": 42,
    "first_name": "John",
    "last_name": "Smith",
    ...
  },
  ...
]
```

> **Note:** List commands backed by an active/inactive status return only **active** records by default. Pass `--status` to override - e.g. `--status Inactive`, or `--status Active --status Inactive` to include both.

## Reference Documentation

This client adheres (to the extent possible) to the API documentation provided by Deltek Ajera, which can be found at:

https://help.deltek.com/product/Ajera/api/index.html

## API reference

Each section below maps a CLI command group to the Ajera API(s) it is built on. The Python client exposes the same operations as `client.<method>()` (e.g. `client.list_employees()`, `client.get_projects(...)`), and `AsyncAjeraClient` exposes every one of them as a coroutine of the same name.

### Employees

Docs: [Employees API](https://help.deltek.com/product/Ajera/api/employees.html) · [List Methods API](https://help.deltek.com/product/Ajera/api/list_methods.html)

`pays`, `payroll-taxes`, and `wage-tables` come from the List Methods API; the rest come from the Employees API.

| Command | Description |
| --- | --- |
| `ajera employees list` | List employees. |
| `ajera employees get <key>...` | Get one or more employees by key. |
| `ajera employees update <key> [options]` | Update simple fields on one employee. |
| `ajera employees types` | List employee types. |
| `ajera employees deductions` | List deductions. |
| `ajera employees fringes` | List fringes. |
| `ajera employees pays` | List pay types. |
| `ajera employees payroll-taxes` | List payroll taxes. |
| `ajera employees wage-tables` | List wage tables. |

> **Note:** `employees list` returns `company_key` and `department_key` as bare integers - the API attaches no names to them. To group employees by department, join `department_key` against the `department_key` of `client.list_departments()` (`ajera departments`).

### Timesheets

Docs: [Timesheets API (v2)](https://help.deltek.com/product/Ajera/api/version2/timesheets.html)

| Command | Description |
| --- | --- |
| `ajera timesheets list` | List timesheets, optionally filtered. |
| `ajera timesheets get <key>...` | Get one or more timesheets by key, with their rows and daily hours. |
| `ajera timesheets create [options]` | Create a timesheet for one employee's week. |
| `ajera timesheets update <key> [options]` | Set daily hours and notes on one row of a timesheet. |
| `ajera timesheets submit <key>... [--unsubmit]` | Submit timesheets for approval, or withdraw them. |

> **Note:** the timesheet methods are only available to an API user with an active authorizing employee set; without one Ajera refuses them. See [setting up an API user](https://learning.deltek.com/bundle/ajera/page/Content/api_setting_up_api_user.htm).

A timesheet covers a week, and its hours live in day slots `D1` through `D7` rather than on dates. `list` returns a summary per week; `get` returns the overhead and project rows behind it.

`update_timesheet` fetches the timesheet for its baseline and submits your edits against it, so the opaque `UnchangedData` the API requires never reaches your code. Each edit names one row and only the days it changes; days you leave out keep their hours:

```python
from ajera import (
    AjeraClient,
    TimesheetOverheadEdit,
    TimesheetProjectEdit,
    TimesheetProjectRowCreate,
)

client = AjeraClient()

client.update_timesheet(
    147,
    overheads=[TimesheetOverheadEdit(overhead_group_detail_key=30, d1_regular=1)],
    projects=[
        # Correct Tuesday on a row that is already on the timesheet.
        TimesheetProjectEdit(
            timesheet_project_key=2, d2_regular=1, d2_notes="Client meeting"
        ),
        # Add a row for work not on it yet.
        TimesheetProjectRowCreate(
            project_key=32, phase_key=33, activity_key=2, d3_regular=4
        ),
    ],
)

client.submit_timesheets([147])
```

The CLI edits one row per invocation, naming its days as `DAY=VALUE`:

```console
$ ajera timesheets update 147 --project-row-key 2 --hours 2=1 --note 2="Client meeting"
```

Overtime is readable but not editable: `UpdateTimesheets` accepts regular hours only, so enter overtime in Ajera directly. There is no API method to delete a timesheet or a row.

### Clients

Docs: [Clients API](https://help.deltek.com/product/Ajera/api/clients.html)

| Command | Description |
| --- | --- |
| `ajera clients list` | List clients. |
| `ajera clients get <key>...` | Get one or more clients by key. |
| `ajera clients update <key> [options]` | Update simple fields on one client. |
| `ajera clients types` | List client types. |

### Contacts

Docs: [Contacts API](https://help.deltek.com/product/Ajera/api/contacts.html)

| Command | Description |
| --- | --- |
| `ajera contacts list` | List contacts. |
| `ajera contacts get <key>...` | Get one or more contacts by key. |
| `ajera contacts update <key> [options]` | Update simple fields on one contact. |
| `ajera contacts types` | List contact types. |

### Vendors

Docs: [Vendors API](https://help.deltek.com/product/Ajera/api/vendors.html) · [Vendor Invoices API (v2)](https://help.deltek.com/product/Ajera/api/version2/vendor_invoices.html)

The `invoices` subcommands come from the Vendor Invoices (v2) API; the rest come from the Vendors API.

| Command | Description |
| --- | --- |
| `ajera vendors list` | List vendors. |
| `ajera vendors get <key>...` | Get one or more vendors by key. |
| `ajera vendors update <key> [options]` | Update simple fields on one vendor. |
| `ajera vendors types` | List vendor types. |
| `ajera vendors invoices list` | List vendor invoices, optionally filtered. |
| `ajera vendors invoices get <key>...` | Get one or more vendor invoices, with their line items. |
| `ajera vendors invoices create [options]` | Create a vendor invoice with a single line item. |

Ajera reports no payment property on a vendor invoice: paid, unpaid, and voided exist only as list filters. Passing `--with-payment-status` (or `with_payment_status=True` to `list_vendor_invoices`) derives it and fills in each invoice's `payment` field with `Paid`, `Unpaid`, or `Voided`. It costs one extra request, so the field stays `null` unless you ask for it:

```python
for invoice in client.list_vendor_invoices(with_payment_status=True):
    print(invoice.vendor_invoice_key, invoice.payment)
```

### Projects

Docs: [Projects API (v2)](https://help.deltek.com/product/Ajera/api/version2/projects.html) · [Projects API (v1)](https://help.deltek.com/product/Ajera/api/projects.html) · [List Methods API](https://help.deltek.com/product/Ajera/api/list_methods.html)

`list`, `get`, `update`, and `create` use the v2 Projects API; `totals`, `types`, and `templates` use the v1 Projects API; `chargeable-phases` comes from the List Methods API.

| Command | Description |
| --- | --- |
| `ajera projects list` | List projects, optionally filtered. |
| `ajera projects get <key>...` | Get one or more projects by key. |
| `ajera projects create <description> [options]` | Create a new project. |
| `ajera projects update <key> [options]` | Update simple fields on one project. |
| `ajera projects totals <key>` | Get a project's financial totals. |
| `ajera projects types` | List project types. |
| `ajera projects templates list` | List project templates, optionally filtered. |
| `ajera projects templates get <key>...` | Get one or more project templates by key. |
| `ajera projects chargeable-phases <project-key>` | List the chargeable phases of a project. |

### General Ledger

Docs: [GL Accounts API](https://help.deltek.com/product/Ajera/api/gl_accounts.html) · [List Methods API](https://help.deltek.com/product/Ajera/api/list_methods.html)

`account-groups` comes from the List Methods API; `list` and `get` come from the GL Accounts API.

| Command | Description |
| --- | --- |
| `ajera ledger list` | List general ledger accounts. |
| `ajera ledger get [id]...` | Get general ledger account details, with calculated amounts. |
| `ajera ledger account-groups` | List general ledger account groups. |

### Reference lists

Docs: [List Methods API](https://help.deltek.com/product/Ajera/api/list_methods.html)

Lightweight lookup lists. (Other List Methods endpoints are grouped with their domain - see `employees`, `ledger`, and `projects` above.)

| Command | Description |
| --- | --- |
| `ajera activities` | List activities. |
| `ajera bank-accounts` | List bank accounts. |
| `ajera companies` | List companies. |
| `ajera departments` | List departments. |
| `ajera invoice-formats` | List invoice formats. |
| `ajera rate-tables` | List rate tables. |
