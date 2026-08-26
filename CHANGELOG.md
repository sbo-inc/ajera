# Changelog

## [0.5.0] - 2026-08-26

- **Fixed:** every call except `CreateAPISession` raised an error on success. Ajera answers `ResponseCode: 200` only for the session call, and `0` for every other method. The envelope decoder treated any other code as a failure. A non-empty `Errors` array now decides, because the code `0` can also carry a failure ([#27]).

## [0.4.0] - 2026-08-22

- Timesheets: list, get, create, update, and submit. The CLI gets matching `ajera timesheets` commands ([#1]).

## [0.3.0] - 2026-08-01

- `AsyncAjeraClient` is a new asyncio client. It mirrors `AjeraClient` method for method, so async callers can `asyncio.gather` requests instead of wrapping each one in `asyncio.to_thread`. Gathered calls share one connection pool and mint one session token ([#10]).
- **Breaking:** `httpx` replaces `requests`, and is now a required dependency. `AjeraClient.session` is a `httpx.Client`, available as `client.http` and deprecated under its old name. `retries` accepts only an `int`, because a `urllib3.Retry` no longer works. The CLI now reports the `httpx` transport errors that were generic failures before ([#10]).
- `AjeraClient` gets `close()` and context-manager support. The async client gets `aclose()` and `async with` ([#10]).
- **Breaking:** `Employee.company` and `Employee.department` are now `company_key` and `department_key`, to match `EmployeeDetails`. The JSON keys from `ajera employees list` change too ([#11]).
- `list_vendor_invoices(with_payment_status=True)` fills a derived `VendorInvoice.payment`. Ajera exposes the payment status only as a list filter. This costs one more request ([#15]).
- `Performance.contract_total` is now serialized, so `backlog` and the contract ratios survive a JSON round trip ([#12]).
- `ProjectTotalsDetails` now accepts python field names. It keeps a `Totals` map that you supply ([#13]).
- Corrected the `VendorInvoice` docs. `ListVendorInvoices` also returns the vendor type, but only when the vendor has one ([#14]).
- The README links to the package on PyPI. It shows badges for the version, the supported Python versions, and the license ([#7]).

## [0.2.0] - 2026-07-18

- **Breaking:** the identifier names now use `key` for surrogate identifiers, and keep `id` for business numbers. The `get_*` methods and their CLI commands rename `*_ids` to `*_keys` ([#8]).

## [0.1.7] - 2026-07-18

- `AjeraClient` now accepts a request timeout and a count of connection retries ([#3]).
- A `session info` command shows the details of the active API session.
- Adds CHANGELOG.md to the repo ([#5]).

## [0.1.6] - 2026-06-27

- A `py.typed` marker gives consumers the type information for the package.
- The package root re-exports the public schema types for consumer type hints.

## [0.1.5] - 2026-06-26

- The PyPI metadata gets project URLs, a license, keywords, and version classifiers.
- The publish workflow now checks that the tag matches the package version before it releases.

## [0.1.4] - 2026-06-26

- Initial release.

[0.4.0]: https://github.com/sbo-inc/ajera/releases/tag/v0.4.0
[0.3.0]: https://github.com/sbo-inc/ajera/releases/tag/v0.3.0
[0.2.0]: https://github.com/sbo-inc/ajera/releases/tag/v0.2.0
[0.1.7]: https://github.com/sbo-inc/ajera/releases/tag/v0.1.7
[0.1.6]: https://github.com/sbo-inc/ajera/releases/tag/v0.1.6
[0.1.5]: https://github.com/sbo-inc/ajera/releases/tag/v0.1.5
[0.1.4]: https://github.com/sbo-inc/ajera/releases/tag/v0.1.4
[#1]: https://github.com/sbo-inc/ajera/issues/1
[#3]: https://github.com/sbo-inc/ajera/issues/3
[#5]: https://github.com/sbo-inc/ajera/issues/5
[#7]: https://github.com/sbo-inc/ajera/issues/7
[#8]: https://github.com/sbo-inc/ajera/issues/8
[#10]: https://github.com/sbo-inc/ajera/issues/10
[#11]: https://github.com/sbo-inc/ajera/issues/11
[#12]: https://github.com/sbo-inc/ajera/issues/12
[#13]: https://github.com/sbo-inc/ajera/issues/13
[#14]: https://github.com/sbo-inc/ajera/issues/14
[#15]: https://github.com/sbo-inc/ajera/issues/15
[#27]: https://github.com/sbo-inc/ajera/issues/27
