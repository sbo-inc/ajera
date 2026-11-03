# Changelog

## [0.10.1] - 2026-11-02

- `ProjectTotals` notes say which totals neither date changes (receipts, billed to date, payments, vendor invoiced), that the billed-by-date columns are signed against the billed ones, and that the outstanding and aging columns follow `EndDate` ([#38]).

## [0.10.0] - 2026-11-02

- `FieldSchema.note` says what a column holds where its name does not. `describe()` returns it, and `ajera odbc describe` prints it ([#36]).
- Notes on the `AxFinancials` functions, `ProjectTotals`, and `GLFullAccountWithCutoff`: what period each amount covers, and whether `StartDate` changes it, as checked live ([#36]).

## [0.9.0] - 2026-11-02

- Function models record the parameters a function ignores: `Source.ignored_parameters` always, `Source.ignored_when` under some codes, and `parameter_filters` for the field to filter on instead. `describe()`, `ajera odbc describe`, and the typed method docstrings show them ([#34]).
- Passing a value to an ignored parameter logs a warning on the `ajera.odbc.arguments` logger. The call still runs ([#34]).
- `ReceiptTotals` ignores its dates, and the seven `TotalType` functions ignore theirs when `TotalType` is 0 ([#34]).
- **Fixed:** None for a function's date parameter failed with `HY104`. It now passes as `NULL` ([#34]).

## [0.8.0] - 2026-11-02

- `AjeraOdbc.closing`, `sessions`, and `wait_closed()` report and wait for sessions still closing after a timeout ([#32]).
- **Breaking:** function arguments are checked against their SQL types and raise `TypeError` or `ValueError` instead of being converted silently: `2026` for a date ran as 1905-07-20 ([#32]).
- `Source.parameter_types` and `describe(model).parameter_types` give each function parameter's SQL type ([#32]).
- **Fixed:** `ajera odbc call` and `count` read `2026` given for a date as a Unix timestamp ([#32]).

## [0.7.0] - 2026-11-01

- `AjeraOdbc.aggregate` totals on the server with `sum_`, `count`, `count_distinct`, `min_`, `max_`, and `avg`, and groups dates by day, week, month, quarter, or year ([#30]).
- `AjeraOdbc.rows` reads only the named fields, plus the primary key ([#30]).
- `after=` resumes a keyed read after a given key ([#30]).
- `current=True` keeps only the current version of rows Ajera keeps versions of ([#30]).
- `timeout=` sets the query timeout for one call ([#30]).
- `describe(model)` and `ajera odbc describe` describe a source offline, with Deltek's code labels ([#30]).
- `Source.sensitive` and `SENSITIVE_COLUMNS` name the columns that must not be logged ([#30]).
- **Fixed:** a timed-out statement raised only once Deltek's server finished it. It now raises on time ([#30]).

## [0.6.0] - 2026-11-01

- New `ajera[odbc]` extra: `AjeraOdbc` and `ajera odbc` read the Ajera database through Deltek's read-only ODBC access, with typed models for every table, view, and function ([#25]).
- Supports Python 3.15, with updated dependencies.

## [0.5.0] - 2026-08-26

- Supports Python 3.14 ([#26]).
- **Fixed:** every call except `CreateAPISession` raised an error on success ([#27]).

## [0.4.0] - 2026-08-22

- Timesheets: list, get, create, update, and submit, with matching `ajera timesheets` commands ([#1]).

## [0.3.0] - 2026-08-01

- `AsyncAjeraClient` mirrors `AjeraClient` for asyncio. Gathered calls share one connection pool and session token ([#10]).
- **Breaking:** `httpx` replaces `requests`. `AjeraClient.session` is now `client.http`, with the old name deprecated, and `retries` takes only an `int` ([#10]).
- Both clients close explicitly or as context managers ([#10]).
- **Breaking:** `Employee.company` and `Employee.department` are now `company_key` and `department_key`, in `ajera employees list` output too ([#11]).
- `list_vendor_invoices(with_payment_status=True)` fills `VendorInvoice.payment`, for one more request ([#15]).
- `Performance.contract_total` is now serialized ([#12]).
- `ProjectTotalsDetails` accepts Python field names ([#13]).
- Corrected the `VendorInvoice` docs ([#14]).
- README badges for PyPI, Python versions, and license ([#7]).

## [0.2.0] - 2026-07-18

- **Breaking:** surrogate identifiers are named `key`, and business numbers keep `id`. The `get_*` methods and CLI commands take `*_keys` instead of `*_ids` ([#8]).

## [0.1.7] - 2026-07-18

- `AjeraClient` takes a request timeout and a count of connection retries ([#3]).
- A `session info` command shows the active API session.
- Adds CHANGELOG.md ([#5]).

## [0.1.6] - 2026-06-27

- Ships a `py.typed` marker, and the package root re-exports the public schema types.

## [0.1.5] - 2026-06-26

- PyPI metadata gets project URLs, a license, keywords, and classifiers. Publishing checks that the tag matches the package version.

## [0.1.4] - 2026-06-26

- Initial release.

[0.10.1]: https://github.com/sbo-inc/ajera/releases/tag/v0.10.1
[0.10.0]: https://github.com/sbo-inc/ajera/releases/tag/v0.10.0
[0.9.0]: https://github.com/sbo-inc/ajera/releases/tag/v0.9.0
[0.8.0]: https://github.com/sbo-inc/ajera/releases/tag/v0.8.0
[0.7.0]: https://github.com/sbo-inc/ajera/releases/tag/v0.7.0
[0.6.0]: https://github.com/sbo-inc/ajera/releases/tag/v0.6.0
[0.5.0]: https://github.com/sbo-inc/ajera/releases/tag/v0.5.0
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
[#25]: https://github.com/sbo-inc/ajera/issues/25
[#26]: https://github.com/sbo-inc/ajera/issues/26
[#27]: https://github.com/sbo-inc/ajera/issues/27
[#30]: https://github.com/sbo-inc/ajera/issues/30
[#32]: https://github.com/sbo-inc/ajera/issues/32
[#34]: https://github.com/sbo-inc/ajera/issues/34
[#36]: https://github.com/sbo-inc/ajera/issues/36
[#38]: https://github.com/sbo-inc/ajera/issues/38
