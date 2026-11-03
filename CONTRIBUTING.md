# Contributing

How to work on this repository. The [README](README.md) covers using the package.

## Setup

The repository uses [uv](https://docs.astral.sh/uv/) and a Makefile; `make help` lists every target.

```bash
make install   # sync the locked environment, with every extra (pyodbc included)
make check     # ruff and mypy
make format    # apply formatting and lint fixes
make test      # offline unit tests
make coverage  # unit tests with coverage (80% minimum)
make build     # build the sdist and wheel
```

`pyodbc` builds against `unixODBC`, so install it first (`unixodbc-dev` on Debian and Ubuntu, `brew install unixodbc` on macOS). `make lock`, `make upgrade`, and `make outdated` manage the locked dependencies.

## REST integration tests

`make test-integration` runs the tests against a live Ajera API. It needs `AJERA_API_URL`, `AJERA_API_USERNAME`, and `AJERA_API_PASSWORD`.

## ODBC

Progress builds the Hybrid Data Pipeline ODBC driver for `x86_64` Linux and Windows only, so ODBC work runs in a `linux/amd64` image (`docker/odbc/Dockerfile`). On Apple Silicon it runs emulated.

```bash
make odbc-image   # download Deltek's driver, verify its checksum, build the image
make odbc-shell   # a shell in the image, with this checkout mounted at /src
make test-odbc    # the live ODBC tests, in the image
make odbc-verify  # validate every model against every live row (ARGS=name filter)
```

Set `AJERA_ODBC_DATASOURCE`, `AJERA_ODBC_USERNAME`, and `AJERA_ODBC_PASSWORD` first; the REST variables enable the tests that compare the two. The Makefile passes each variable to `docker run` by name, so no value appears on a command line. Never commit credentials, the driver, or the schema workbook.

Deltek exposes only the production database. Keep live checks to metadata, counts, and timings, and never print row contents: reduce a comparison to a bool before asserting it, and run with `--tb=no` when a failure could show values.

### Refreshing the generated models

The database models, enums, and typed function methods are generated; never edit them by hand. For a new Ajera release:

1. `make odbc-catalog` snapshots the live catalog into `scripts/odbc/catalog.json`. Tenant custom fields are left out.
2. `make odbc-probe` records which function parameters have no effect, always or under some `TotalType` codes, and which amount columns change with `StartDate`. A full run takes about 40 minutes, so pass a few functions at a time with `ARGS="ReceiptTotals ClientTotals"`. The two GL balance functions are too slow to probe.
3. `make odbc-enums XLSX=path/to/AjeraSchema.xlsx` extracts the documented codes from the schema workbook, exported from Ajera under Setup > Utility > Ajera Schema.
4. `make odbc-generate` regenerates the models and methods from the catalog, the codes, and the column notes in `scripts/odbc/notes.py`. Each note there says what a column holds and how that was checked live. The generator adds the probe's finding on `StartDate`, and it stops on a note for a column that no longer exists.

## Releasing

Bump `version` in `pyproject.toml`, run `uv lock`, and add the release to `CHANGELOG.md`. Pushing a `v*` tag that matches the version builds the package, creates the GitHub release, and publishes to PyPI.
