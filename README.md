[![CI](https://github.com/sbo-inc/ajera/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/sbo-inc/ajera/actions/workflows/ci.yaml)

# Deltek Ajera Python client

A typed Python client and command-line interface for the [Deltek Ajera](https://www.deltek.com/en/project-based-erp/ajera) API.

Ajera exposes a single JSON-RPC style endpoint; this package wraps it in an ergonomic, fully type-hinted client built on [Pydantic](https://docs.pydantic.dev/) models, plus an `ajera` CLI for quick access from the terminal. Responses are validated and normalized into predictable Python objects so you can work with employees, projects, vendors, invoices, and general-ledger data without hand-rolling request payloads.

## Features

- **Typed models** - every response is parsed into Pydantic models with descriptive fields.
- **Python client and CLI** - use it as a library or straight from the shell via `ajera`.
- **Sensible defaults** - handles session tokens and per-method API versions for you.
- **Read and write** - list, get, update, and create across the supported APIs.

## Installation

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

### CLI

```console
$ ajera employees list
[
  {
    "employee_key": 42,
    "first_name": "Ada",
    "last_name": "Lovelace",
    ...
  },
  ...
]
```

> **Note:** List commands backed by an active/inactive status return only **active** records by
> default. Pass `--status` to override - e.g. `--status Inactive`, or
> `--status Active --status Inactive` to include both.

## Reference Documentation

This client adheres (to the extent possible) to the API documentation provided by Deltek Ajera, which can be found at:

https://help.deltek.com/product/Ajera/api/index.html

## API reference

Each section below maps a CLI command group to the Ajera API(s) it is built on. The Python client
exposes the same operations as `client.<method>()` (e.g. `client.list_employees()`,
`client.get_projects(...)`).

### Employees

Docs: [Employees API](https://help.deltek.com/product/Ajera/api/employees.html) · [List Methods API](https://help.deltek.com/product/Ajera/api/list_methods.html)

`pays`, `payroll-taxes`, and `wage-tables` come from the List Methods API; the rest come from the Employees API.

| Command | Description |
| --- | --- |
| `ajera employees list` | List employees. |
| `ajera employees get <id>...` | Get one or more employees by ID. |
| `ajera employees update <key> [options]` | Update simple fields on one employee. |
| `ajera employees types` | List employee types. |
| `ajera employees deductions` | List deductions. |
| `ajera employees fringes` | List fringes. |
| `ajera employees pays` | List pay types. |
| `ajera employees payroll-taxes` | List payroll taxes. |
| `ajera employees wage-tables` | List wage tables. |

### Clients

Docs: [Clients API](https://help.deltek.com/product/Ajera/api/clients.html)

| Command | Description |
| --- | --- |
| `ajera clients list` | List clients. |
| `ajera clients get <id>...` | Get one or more clients by ID. |
| `ajera clients update <key> [options]` | Update simple fields on one client. |
| `ajera clients types` | List client types. |

### Contacts

Docs: [Contacts API](https://help.deltek.com/product/Ajera/api/contacts.html)

| Command | Description |
| --- | --- |
| `ajera contacts list` | List contacts. |
| `ajera contacts get <id>...` | Get one or more contacts by ID. |
| `ajera contacts update <key> [options]` | Update simple fields on one contact. |
| `ajera contacts types` | List contact types. |

### Vendors

Docs: [Vendors API](https://help.deltek.com/product/Ajera/api/vendors.html) · [Vendor Invoices API (v2)](https://help.deltek.com/product/Ajera/api/version2/vendor_invoices.html)

The `invoices` subcommands come from the Vendor Invoices (v2) API; the rest come from the Vendors API.

| Command | Description |
| --- | --- |
| `ajera vendors list` | List vendors. |
| `ajera vendors get <id>...` | Get one or more vendors by ID. |
| `ajera vendors update <key> [options]` | Update simple fields on one vendor. |
| `ajera vendors types` | List vendor types. |
| `ajera vendors invoices list` | List vendor invoices, optionally filtered. |
| `ajera vendors invoices get <key>...` | Get one or more vendor invoices, with their line items. |
| `ajera vendors invoices create [options]` | Create a vendor invoice with a single line item. |

### Projects

Docs: [Projects API (v2)](https://help.deltek.com/product/Ajera/api/version2/projects.html) · [Projects API (v1)](https://help.deltek.com/product/Ajera/api/projects.html) · [List Methods API](https://help.deltek.com/product/Ajera/api/list_methods.html)

`list`, `get`, `update`, and `create` use the v2 Projects API; `totals`, `types`, and `templates`
use the v1 Projects API; `chargeable-phases` comes from the List Methods API.

| Command | Description |
| --- | --- |
| `ajera projects list` | List projects, optionally filtered. |
| `ajera projects get <id>...` | Get one or more projects by ID. |
| `ajera projects create <description> [options]` | Create a new project. |
| `ajera projects update <key> [options]` | Update simple fields on one project. |
| `ajera projects totals <id>` | Get a project's financial totals. |
| `ajera projects types` | List project types. |
| `ajera projects templates list` | List project templates, optionally filtered. |
| `ajera projects templates get <id>...` | Get one or more project templates by ID. |
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

Lightweight lookup lists. (Other List Methods endpoints are grouped with their domain - see
`employees`, `ledger`, and `projects` above.)

| Command | Description |
| --- | --- |
| `ajera activities` | List activities. |
| `ajera bank-accounts` | List bank accounts. |
| `ajera companies` | List companies. |
| `ajera departments` | List departments. |
| `ajera invoice-formats` | List invoice formats. |
| `ajera rate-tables` | List rate tables. |
