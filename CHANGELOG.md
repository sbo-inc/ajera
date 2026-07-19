# Changelog

## [0.2.0] - 2026-07-18

- **Breaking:** standardized identifier vocabulary — surrogate record
  identifiers are now consistently called `key`, reserving `id` for genuine
  business numbers (project number, GL account number, etc.). The `get_*` client
  methods and CLI `get`/`totals` commands renamed their `*_ids` parameters to
  `*_keys` (`get_project_totals` renamed `project_id` to `project_key`).
  Docstrings, CLI help, and schema field descriptions updated to match ([#8]).

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

[0.2.0]: https://github.com/sbo-inc/ajera/releases/tag/v0.2.0
[0.1.7]: https://github.com/sbo-inc/ajera/releases/tag/v0.1.7
[0.1.6]: https://github.com/sbo-inc/ajera/releases/tag/v0.1.6
[0.1.5]: https://github.com/sbo-inc/ajera/releases/tag/v0.1.5
[0.1.4]: https://github.com/sbo-inc/ajera/releases/tag/v0.1.4
[#3]: https://github.com/sbo-inc/ajera/issues/3
[#5]: https://github.com/sbo-inc/ajera/issues/5
[#8]: https://github.com/sbo-inc/ajera/issues/8 