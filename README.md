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
- **ODBC** - `AjeraOdbc` reads the database through Deltek's read-only ODBC access, with typed models for every table, view, and function.

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

### Open Database Connectivity (ODBC)

Deltek supports read-only ODBC access to the Ajera database as a separate entitlement. Its documentation is [ODBC Read Only Access](https://learning.deltek.com/bundle/MaconomyEnterpriseCloudOnlineAdminGuide/page/ODBC_Read_Only_Access.html). `AjeraOdbc` reads the database and returns the same models as the REST client. It never writes. Install the extra:

```bash
pip install 'ajera[odbc]'
```

The reader also needs `unixODBC` and the Progress DataDirect Hybrid Data Pipeline ODBC driver ([Deltek's Linux download](https://dsm.deltek.com/DFVE/ODBC/HDPLinuxDriver.zip)). The driver is built for `x86_64` Linux and Windows only, so on any other machine, including Apple Silicon, run the reader in a `linux/amd64` container.

| Variable | Description |
| --- | --- |
| `AJERA_ODBC_DATASOURCE` | Hybrid Data Pipeline data source, from Deltek's service request. |
| `AJERA_ODBC_USERNAME` | ODBC logon ID. |
| `AJERA_ODBC_PASSWORD` | ODBC password. |
| `AJERA_ODBC_HOST` | Service host (default `ajera-hdp01.prd.mydeltek.com`). |
| `AJERA_ODBC_PORT` | Service port (default `443`). |
| `AJERA_ODBC_DRIVER` | Registered ODBC driver name (default `DataDirect HDP 4.6`). |

The database reaches much further than the REST API. It holds transaction-level detail, accounts receivable, receipts, the general ledger, revenue, payroll, purchase orders and rate values. Every table (165), view (60), and table-valued function (19) has a typed model in `ajera.schemas.database`. Pass a model to `read`, `stream`, `get`, `count`, `rows`, or `aggregate`, or call a function through its typed method:

```python
from datetime import date

from ajera.odbc import AjeraOdbc, between
from ajera.schemas.database import ClientInvoiceRecord, GLDetailRecord, GLDetailType

with AjeraOdbc() as db:
    # Filter by field: a value means =, a list means IN, None means IS NULL.
    invoices = db.read(ClientInvoiceRecord, where={"status": [1, 4]}, limit=100)

    # Millions of rows, a batch at a time.
    for row in db.stream(
        GLDetailRecord,
        where={
            "type": GLDetailType.billed,
            "accounting_date": between(date(2026, 1, 1), date(2026, 3, 31)),
        },
    ):
        ...

    # Ajera's own period-totals functions, with no per-project REST fan-out.
    totals = db.project_totals(date(2026, 1, 1), date(2026, 3, 31))
```

- **Fields** use the REST naming. The table's column prefix is dropped, and keys end in `_key` (`tProject` is `project_key`). The column name works too.
- **Code columns** validate to an `IntEnum` when Ajera documents the code, and stay a plain `int` otherwise.
- **Custom fields** a tenant adds appear on `record.custom_fields`.
- **Binary columns** (invoice snapshots, report designs) are skipped unless you pass `include_blobs=True`.
- **Large reads are paged.** Deltek's pipeline refuses any result over 500,000 rows, so keyed sources are read in pages of 100,000 transparently.
- **Filters** are in `ajera.odbc`: `eq`, `ne`, `lt`, `le`, `gt`, `ge`, `between`, `like`, `in_`, `not_in`, `is_null`, `not_null`.

`aggregate` totals on the server, so a monthly figure never moves every row through the pipeline. `rows` returns only the fields you name, as dictionaries whose values are validated like a full read:

```python
from datetime import date

from ajera.odbc import AjeraOdbc, between, count, sum_
from ajera.schemas.database import (
    ProjectRecord,
    ProjectStatus,
    TransactionActivityType,
    TransactionRecord,
    describe,
)

with AjeraOdbc() as db:
    # Hours per employee per month, counting each transaction's current version once.
    hours = db.aggregate(
        TransactionRecord,
        measures=[sum_("units", alias="hours"), count()],
        group_by=["employee_key", "date:month"],
        where={
            "activity_type": TransactionActivityType.labor,
            "date": between(date(2026, 1, 1), date(2026, 3, 31)),
        },
        current=True,
    )
    # [{"employee_key": 101, "date:month": date(2026, 1, 1), "hours": Decimal("162.5"), "count": 41}, ...]

    # Two of a project's 200 columns. The key always comes along.
    projects = db.rows(
        ProjectRecord,
        fields=["description", "status"],
        where={"status": ProjectStatus.active},
    )
    # [{"project_key": 7, "description": "...", "status": ProjectStatus.active}, ...]

    # Resume after the last key you saw, in this process or another.
    more = db.rows(
        ProjectRecord, fields=["description"], after=projects[-1]["project_key"]
    )

    # A slow function gets a longer timeout for this one call.
    balances = db.gl_balance_totals(date(2026, 3, 31), timeout=900)

# Fields, SQL types, keys, and Deltek's code labels, without a connection.
schema = describe(TransactionRecord)
```

- **Measures** are `sum_`, `count`, `count_distinct`, `min_`, `max_`, and `avg`. Group a date field by period with `field:day`, `field:week`, `field:month`, `field:quarter`, or `field:year`, which return the first day of the period. Weeks start on Monday. As in SQL Server, `avg` of an integer column is an integer.
- **`current=True`** keeps only the current version of each row, for the sources where Ajera keeps edited and deleted rows: `AxTransaction`, `AxGLDetail`, `AxVendorInvoiceApproval`, and the views over them. It raises on any other source. `Source.current_column` and `Source.deleted_column` name the marker columns.
- **`after=`** resumes a read of a source with a single-column key, in key order. It works on `read`, `stream`, and `rows`.
- **`timeout=`** sets the query timeout for one call. A statement that times out raises at once but keeps running on Deltek's server until it finishes. The reader closes that connection in the background and opens a new one, so the login holds one more session meanwhile. `db.closing` counts those sessions, `db.sessions` adds the open one, and `db.wait_closed()` waits for them to close.
- **Function arguments** are checked against each parameter's SQL type before they are sent, because SQL Server converts some mistakes silently: an `int` passed for a date is a day count from 1900. Date parameters take a `date`, a `datetime`, or an ISO 8601 string. `describe(model).parameter_types` lists the types.
- **Ignored parameters.** Some functions declare parameters that do not change their rows. `ReceiptTotals` returns receipts of every date, whatever `StartDate` and `EndDate` say, and the functions with a `TotalType` ignore their dates when it is 0 or NULL, and some under other codes too. `describe(model).ignored_parameters` and `ignored_when` list them, and `parameter_filters` names the field to filter on instead, such as `where={"r_date": between(start, end)}`. Passing any value other than None to one logs a warning on the `ajera.odbc.arguments` logger, whatever `log` is set to, and the call still runs.
- **`AccrualCash`** takes `Accrual` or `Cash`. Any other value, `A` included, returns the same rows as NULL.
- **Schema facts** need no connection. `describe(model)` and `ajera odbc describe SOURCE` give a source's fields, SQL types, keys, and parameters. Each code has a `label` with Deltek's own text (`TransactionStatus.write_off.label` is `"Write Off"`). `Source.sensitive` and `SENSITIVE_COLUMNS` name the columns holding identity numbers, credentials, tokens, and banking details.

The CLI exposes the same reads:

```console
$ ajera odbc sources --kind function
$ ajera odbc describe AxTransaction
$ ajera odbc read AxClientInvoice -w status=1,4 -w "invoice_date>=2026-01-01" -n 50
$ ajera odbc call ProjectTotals 2026-01-01 2026-03-31 -w project_key=1234
```

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
