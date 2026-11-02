# Changelog

## [0.9.0] - 2026-11-02

- `Source.ignored_parameters` and `describe(model).ignored_parameters` list the function parameters that do not change the rows, in call order. `ignored_when` lists those ignored only under some codes. `parameter_filters` names the field to filter on instead, and `parameter_notes` says where that filter does not mean the same. `ajera odbc describe` prints them, and each typed method's docstring names them ([#34]).
- Passing any value other than None to an ignored parameter logs a warning on the `ajera.odbc.arguments` logger, whatever `log` is set to. So does a value passed while its condition holds. The call still runs. This covers `call`, `rows`, `count`, `aggregate`, and the typed function methods ([#34]).
- `make odbc-probe` finds them live. It calls each function again with one argument changed and compares the row count, the sum of every numeric column, and a checksum of every other column. Its findings go into `scripts/odbc/catalog.json`, and `make odbc-catalog` keeps them ([#34]).
- Found live: `ReceiptTotals` ignores `StartDate` and `EndDate`; filter on `r_date` instead. The seven functions with a `TotalType` ignore their dates when it is 0, and some under other codes too: `ClientTotals(0, start, end)` returns the same totals for any dates. No other parameter is ignored. `AxGLBalanceTotals` and `GLFullAccountWithCutoff` are too slow to probe ([#34]).
- **Fixed:** passing None for a function's date parameter failed with `HY104`, because the HDP driver refuses a NULL bound to a date parameter. A None argument now goes into the statement as `NULL`. Callers can now pass None for an ignored date, which is what the warning advises ([#34]).

## [0.8.0] - 2026-11-02

- `AjeraOdbc.closing` counts the sessions still closing after a timeout, `AjeraOdbc.sessions` adds the open one, and `AjeraOdbc.wait_closed()` waits for them. A timed-out session stays held until Deltek's server finishes the abandoned statement, so a caller with few seats can now see and wait for it ([#32]).
- **Breaking:** function arguments are checked against each parameter's SQL type before they are bound. SQL Server converted some mistakes silently: `2026` passed for a date ran as 1905-07-20, and a string longer than a `varchar` parameter was cut short. Such calls now raise `TypeError` or `ValueError`. Date parameters still take an ISO 8601 string ([#32]).
- `Source.parameter_types` and `describe(model).parameter_types` give each function parameter's SQL declaration, such as `varchar(10)` or `decimal(19,2)`. `ajera odbc describe` prints them ([#32]).
- **Fixed:** `ajera odbc call` and `ajera odbc count` read a number given for a date argument as a Unix timestamp, so `2026` became 1970-01-01. They now read each argument by its SQL type and refuse that ([#32]).

## [0.7.0] - 2026-11-01

- `AjeraOdbc.aggregate` totals on the server with `GROUP BY`. The measures are `sum_`, `count`, `count_distinct`, `min_`, `max_`, and `avg`, and date fields group by `day`, `week`, `month`, `quarter`, or `year`. A monthly total no longer moves every row through Deltek's pipeline ([#30]).
- `AjeraOdbc.rows` reads only the named fields. Rows are dictionaries whose values validate like a full read, and the primary key always comes along ([#30]).
- `after=` on `read`, `stream`, and `rows` resumes a keyed read after a key, so a long read can continue in another request or process ([#30]).
- `current=True` on `read`, `stream`, `rows`, `count`, and `aggregate` keeps only the current version of each row, for the sources where Ajera keeps edited and deleted rows. `Source.current_column` and `Source.deleted_column` name the marker columns ([#30]).
- `timeout=` sets the query timeout for one call. It works on `read`, `stream`, `rows`, `count`, `get`, `call`, `aggregate`, and every typed function method ([#30]).
- `describe(model)` and `ajera odbc describe` describe a source offline: its fields, SQL types, keys, foreign keys, and Deltek's documented code labels. Each code has a `label`, and `CODE_LABELS` holds them all ([#30]).
- The sensitive-column classification is public: `Source.sensitive`, `SENSITIVE_COLUMNS`, and `json_schema_extra={"sensitive": True}` on each such field. Each field also records its `sql_type` there ([#30]).
- **Fixed:** a statement that ran past the query timeout raised only once Deltek's server finished it, because closing its connection waited for the server. The connection now closes in the background, so the timeout raises on time ([#30]).

## [0.6.0] - 2026-11-01

- `ajera[odbc]` is a new optional extra. `AjeraOdbc` reads the Ajera database read-only through Deltek's ODBC entitlement into typed models for every table, view, and table-valued function, and `ajera odbc` brings the same reads to the CLI ([#25]).
- Python 3.15 is now tested in CI and declared in the package metadata, and the locked dependencies are updated.

## [0.5.0] - 2026-08-26

- Python 3.14 is now tested in CI and declared in the package metadata, so the supported-versions badge and the PyPI classifiers list it ([#26]).
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
[#25]: https://github.com/sbo-inc/ajera/issues/25
[#26]: https://github.com/sbo-inc/ajera/issues/26
[#27]: https://github.com/sbo-inc/ajera/issues/27
[#30]: https://github.com/sbo-inc/ajera/issues/30
[#32]: https://github.com/sbo-inc/ajera/issues/32
[#34]: https://github.com/sbo-inc/ajera/issues/34
