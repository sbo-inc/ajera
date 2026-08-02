# Changelog

## [0.3.0] - 2026-08-01

- `AsyncAjeraClient`, an asyncio client mirroring `AjeraClient` method for method, so async callers can `asyncio.gather` requests instead of wrapping each one in `asyncio.to_thread`. Gathered calls share one connection pool and mint a single session token ([#10]).
- **Breaking:** `requests` is replaced by `httpx`, which is now a required dependency. `AjeraClient.session` is a `httpx.Client`, available as `client.http` and deprecated under its old name; `retries` accepts only an `int` (a `urllib3.Retry` is no longer supported); and the CLI reports `httpx` transport errors that previously surfaced as generic failures ([#10]).
- `AjeraClient` gained `close()` and context-manager support, alongside the async client's `aclose()` and `async with` ([#10]).
- **Breaking:** `Employee.company` and `Employee.department` renamed to `company_key` and `department_key`, matching `EmployeeDetails`. `ajera employees list` JSON keys change to match ([#11]).
- `list_vendor_invoices(with_payment_status=True)` populates a derived `VendorInvoice.payment`, which Ajera exposes only as list filters. Costs one extra request ([#15]).
- `Performance.contract_total` is now serialized, so `backlog` and the contract ratios survive a JSON round trip ([#12]).
- `ProjectTotalsDetails` now accepts python field names and keeps an explicitly supplied `Totals` map ([#13]).
- Corrected `VendorInvoice` docs: `ListVendorInvoices` returns vendor type too, but only when the vendor has one assigned ([#14]).

## [0.2.0] - 2026-07-18

- **Breaking:** standardized identifier vocabulary on `key` for surrogate identifiers, reserving `id` for business numbers. The `get_*` methods and their CLI commands renamed `*_ids` to `*_keys` ([#8]).

## [0.1.7] - 2026-07-18

- Configurable request timeout and connection retries on `AjeraClient` ([#3]).
- `session info` command to display details about the active API session.
- Add CHANGELOG.md to repo ([#5]).

## [0.1.6] - 2026-06-27

- `py.typed` marker so consumers get type information for the package.
- Re-exported public schema types from the package root for consumer type hints.

## [0.1.5] - 2026-06-26

- Project URLs, license, keywords, and version classifiers to the PyPI metadata.

- Publish workflow now verifies the tag matches the package version before releasing.

## [0.1.4] - 2026-06-26

- Initial release.

[0.3.0]: https://github.com/sbo-inc/ajera/releases/tag/v0.3.0
[0.2.0]: https://github.com/sbo-inc/ajera/releases/tag/v0.2.0
[0.1.7]: https://github.com/sbo-inc/ajera/releases/tag/v0.1.7
[0.1.6]: https://github.com/sbo-inc/ajera/releases/tag/v0.1.6
[0.1.5]: https://github.com/sbo-inc/ajera/releases/tag/v0.1.5
[0.1.4]: https://github.com/sbo-inc/ajera/releases/tag/v0.1.4
[#3]: https://github.com/sbo-inc/ajera/issues/3
[#5]: https://github.com/sbo-inc/ajera/issues/5
[#8]: https://github.com/sbo-inc/ajera/issues/8
[#10]: https://github.com/sbo-inc/ajera/issues/10
[#11]: https://github.com/sbo-inc/ajera/issues/11
[#12]: https://github.com/sbo-inc/ajera/issues/12
[#13]: https://github.com/sbo-inc/ajera/issues/13
[#14]: https://github.com/sbo-inc/ajera/issues/14
[#15]: https://github.com/sbo-inc/ajera/issues/15 
