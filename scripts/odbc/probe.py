"""
Find the function parameters that have no effect on the rows.

Each function is called with base arguments, then again with one parameter
changed and the others held, and the two results are compared by a
fingerprint the server computes: the row count, the sum of every numeric
column, and a checksum of every other column. Only the fingerprint leaves the
server, never a row, and the script prints only names, row counts, and
verdicts. Run it in the ODBC image with the `AJERA_ODBC_*` variables set,
then regenerate:

    make odbc-probe ARGS="ReceiptTotals RefundTotals"
    make odbc-generate

How a verdict is reached:
- A parameter is tried with other values and with None. A date moves
  within the base year and into another year, and two date ranges that do
  not overlap are also tried when neither date changed anything alone.
- A code or key that the function reads as a word or a real row is given
  one: `AccrualCash` takes `Accrual` or `Cash`, and anything else, `A`
  included, returns the same rows as NULL.
- A code parameter (`TotalType`) can change what the dates mean, so the
  other parameters are probed again under each code that returns different
  rows.
- A parameter has no effect when no change to it changed the fingerprint,
  in any of those. None is among the changes, so a caller can always pass
  None to one.
- A parameter that has an effect under some codes but none under others is
  recorded with those codes: `TotalType` 0 makes most totals functions
  ignore their dates.
- A comparison where both calls return no rows proves nothing. A parameter
  with only such comparisons is unchecked, not "no effect".
- The database is live, and rows change while a slow function is probed.
  So a difference counts only once it shows again on two fresh calls, back
  to back. An edit can make a result look changed, but never unchanged.

The verdicts go into `catalog.json` as `ignored_parameters`,
`unchecked_parameters`, and `ignored_when`, with `parameter_filters` and
`parameter_notes` from
`FILTERS` for the ignored ones. A filter is written only after it is shown to
narrow the function's rows. Only the functions probed are rewritten.
"""

import json
import logging
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from harvest import dump

from ajera.odbc import AjeraOdbc, between
from ajera.odbc.queries.select import quote_name, source_clause
from ajera.schemas.database import FUNCTIONS, TABLES, DatabaseRecord

CATALOG = Path(__file__).resolve().parent / "catalog.json"

# The base date range is a closed year with activity. Refunds are rare, so
# `RefundTotals` is probed over its whole history.
RANGE = (date(2025, 1, 1), date(2025, 12, 31))
RANGES = {"RefundTotals": (date(2000, 1, 1), date(2026, 10, 31))}
# A range that does not overlap the base one, and a key no row holds: a
# filter that is applied returns nothing for it.
OTHER_RANGE = (date(2023, 3, 1), date(2023, 3, 31))
NO_KEY = 2**31 - 1

# Each parameter's base value and the values tried in its place, by name.
# Dates come from `dates`.
VALUES: dict[str, tuple[object, Sequence[object]]] = {
    "Minimum": (Decimal(0), [Decimal(1_000_000)]),
    "CloseYear": (False, [True]),
    # The functions compare the whole word. Any other value, `A` and `C`
    # included, returns the same rows as NULL.
    "AccrualCash": ("Accrual", ["Cash"]),
    "Client": (None, [NO_KEY]),
    "Project": (None, [NO_KEY]),
    "IncludeVoidedNSF": (False, [True]),
    # Codes 4 and up return no rows, or the same rows as 0.
    "TotalType": (0, [1, 2, 3]),
    # A company no row holds returns the same rows as NULL, which differ from
    # a real company's, so the base is a real one: `add_live_values`.
    "pCompany": (None, [NO_KEY]),
    # The latest credit memo, so the function has rows: `add_live_values`.
    "Receipt": (None, [NO_KEY]),
}
# Parameters that change what the others mean.
CODES = frozenset({"TotalType"})
DATE_RANGE = ("StartDate", "EndDate")

# Each sums the whole ledger up to its cutoff, for minutes, on a server that
# keeps running a statement after the client gives up on it.
SLOW = frozenset({"AxGLBalanceTotals", "GLFullAccountWithCutoff"})


@dataclass(frozen=True)
class Filter:
    """What to filter on in place of ignored parameters, and its caveat."""

    column: str
    note: str | None = None


# The column a `where` filters on in place of each ignored parameter. Checked
# live before it is written: filtering on it must narrow the rows.
FILTERS: dict[str, dict[str, Filter]] = {
    "ReceiptTotals": {
        "StartDate": Filter("rDate"),
        "EndDate": Filter("rDate"),
    },
}

NUMERIC = frozenset(
    {"int", "smallint", "tinyint", "bigint", "decimal", "numeric"}
    | {"money", "smallmoney", "float", "real"}
)

# Column types BINARY_CHECKSUM refuses.
UNCHECKSUMMED = frozenset({"text", "ntext", "image", "xml"})

type Fingerprint = tuple[Any, ...]


# =============================================================================
# Fingerprints
# =============================================================================


def fingerprint_columns(model: type[DatabaseRecord]) -> list[tuple[str, str]]:
    """Each column the fingerprint covers, with its aggregate: a sum or a checksum."""
    covered = []
    for name, info in model.model_fields.items():
        extra = (
            info.json_schema_extra if isinstance(info.json_schema_extra, dict) else {}
        )
        column = info.alias or name
        if extra.get("sql_type") in NUMERIC:
            aggregate = f"SUM(CAST({quote_name(column)} AS decimal(38, 6)))"
        elif extra.get("sql_type") in UNCHECKSUMMED:
            continue
        else:
            aggregate = f"CHECKSUM_AGG(BINARY_CHECKSUM({quote_name(column)}))"
        covered.append((column, aggregate))
    return covered


@dataclass
class Fingerprints:
    """
    Fingerprints of one function's results, each computed once.

    A fingerprint is the row count and one aggregate per column. Columns that
    differ between two identical calls (a clock, a running balance) are left
    out of every comparison once `settle` finds them.
    """

    db: AjeraOdbc
    model: type[DatabaseRecord]
    seen: dict[tuple[object, ...], Fingerprint] = field(default_factory=dict)
    volatile: list[str] = field(default_factory=list)
    calls: int = 0

    def __post_init__(self) -> None:
        self.columns = fingerprint_columns(self.model)

    def raw(self, arguments: tuple[object, ...], fresh: bool = False) -> Fingerprint:
        if fresh or arguments not in self.seen:
            target, parameters = source_clause(self.model, arguments)
            aggregates = ", ".join(a for _, a in self.columns)
            cursor = self.db.connection.cursor()
            try:
                cursor.execute(
                    f"SELECT COUNT_BIG(*), {aggregates} FROM {target}", *parameters
                )
                self.seen[arguments] = tuple(cursor.fetchall()[0])
            except Exception as error:  # noqa: BLE001
                # A refused argument is a change in behavior, not a crash.
                self.seen[arguments] = ("error", _sqlstate(error))
            finally:
                cursor.close()
            self.calls += 1
        return self.seen[arguments]

    def settle(self, base: tuple[object, ...]) -> None:
        """Call the base twice, and leave out the columns that moved."""
        first, second = self.raw(base), self.raw(base, fresh=True)
        if first[0] == "error" or second[0] == "error":
            return
        self.volatile = [
            column
            for (column, _), a, b in zip(
                self.columns, first[1:], second[1:], strict=True
            )
            if a != b
        ]

    def explain(self, base: Fingerprint, other: Fingerprint) -> str:
        """How two fingerprints differ, by row count or by column name only."""
        if base[0] == "error" or other[0] == "error":
            before, after = (
                f[-1] if f[0] == "error" else "rows" for f in (base, other)
            )
            return f"{before} -> {after}"
        if base[0] != other[0]:
            return f"rows {base[0]} -> {other[0]}"
        kept = [c for c, _ in self.columns if c not in self.volatile]
        moved = [c for c, a, b in zip(kept, base[1:], other[1:], strict=True) if a != b]
        return f"same rows; {len(moved)} columns moved: {', '.join(moved[:6])}"

    def __call__(
        self, arguments: tuple[object, ...], fresh: bool = False
    ) -> Fingerprint:
        fingerprint = self.raw(arguments, fresh)
        if fingerprint[0] == "error":
            return fingerprint
        return (fingerprint[0],) + tuple(
            value
            for (column, _), value in zip(self.columns, fingerprint[1:], strict=True)
            if column not in self.volatile
        )


def _sqlstate(error: Exception) -> str:
    state = error.args[0] if error.args else ""
    if state == "HYT00":
        # The connection is stuck behind the abandoned statement.
        raise error
    return (
        str(state)
        if isinstance(state, str) and len(state) == 5
        else type(error).__name__
    )


def rows(fingerprint: Fingerprint) -> int:
    return int(fingerprint[0]) if fingerprint[0] != "error" else 0


# =============================================================================
# Verdicts
# =============================================================================


@dataclass
class Evidence:
    """What changing one parameter did: changed, unchanged, or both empty."""

    changed: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    empty: list[str] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        if self.changed:
            return "applied"
        return "no effect" if self.unchanged else "unchecked"


@dataclass
class Probed:
    """
    One function's evidence, by parameter and by the code it was probed under.

    Attributes:
        evidence: Parameter, then the label of the code context (`TotalType=2`,
            or empty without codes), to what changing it did there.
        code: The code parameter (`TotalType`), if the function has one.
        codes: Each context's label, to every code value that returned that
            context's rows. A code whose rows match another's at the base
            dates is not probed again: the base range is one year of many, so
            had that code applied the dates, its rows would differ.
    """

    evidence: dict[str, dict[str, Evidence]]
    code: str | None = None
    codes: dict[str, list[object]] = field(default_factory=dict)


def compare(
    fingerprint: Fingerprints,
    evidence: Evidence,
    label: str,
    base: tuple[object, ...],
    other: tuple[object, ...],
) -> None:
    """
    Record what calling with `other` instead of `base` did.

    A difference is confirmed on two fresh calls, back to back, before it
    counts: rows edited between the first two calls must not pass for the
    parameter's effect. A real effect shows again; an edit in between does not.
    """
    if fingerprint(base) != fingerprint(other):
        fingerprint(base, fresh=True)
        fingerprint(other, fresh=True)
    before, after = fingerprint(base), fingerprint(other)
    if before != after:
        evidence.changed.append(f"{label}: {fingerprint.explain(before, after)}")
    elif rows(before) == 0:
        evidence.empty.append(label)
    else:
        evidence.unchanged.append(label)


def add_live_values(db: AjeraOdbc) -> None:
    """Fill in the values only the database knows: a company and a credit memo."""
    companies = db.rows(TABLES["AxCompany"], fields=["cmpKey"], limit=1)
    if companies:
        VALUES["pCompany"] = (companies[0]["company_key"], [NO_KEY])
    memos = db.rows(
        TABLES["AxReceipt"],
        fields=["rKey"],
        where={"rType": 2},
        order_by=["-rKey"],
        limit=1,
    )
    if memos:
        VALUES["Receipt"] = (memos[0]["receipt_key"], [NO_KEY])


def month_end(day: date) -> date:
    return (day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)


def dates(name: str, start: date, end: date) -> tuple[object, Sequence[object]]:
    """
    A date parameter's base value and the values tried in its place.

    Each date moves within the base year and into another year, because some
    functions read a date only for its month or its fiscal year.
    """
    if name == "StartDate":
        return start, [end.replace(day=1), start.replace(year=start.year - 1)]
    if name == "EndDate":
        return end, [month_end(start), end.replace(year=end.year + 1)]
    return end, [end.replace(year=end.year - 2)]


def plan(
    model: type[DatabaseRecord],
) -> dict[str, tuple[object, Sequence[object]]] | None:
    """Each parameter's base value and alternatives; None when one is unknown."""
    start, end = RANGES.get(model.__source__.name, RANGE)
    values = {}
    for name in model.__source__.parameters:
        if name in ("StartDate", "EndDate", "CutoffDate"):
            values[name] = dates(name, start, end)
        elif name in VALUES:
            values[name] = VALUES[name]
        else:
            return None
    return values


def base_arguments(model: type[DatabaseRecord]) -> tuple[object, ...] | None:
    values = plan(model)
    return None if values is None else tuple(base for base, _ in values.values())


def replaced(
    parameters: Sequence[str], arguments: tuple[object, ...], name: str, value: object
) -> tuple[object, ...]:
    index = parameters.index(name)
    return (*arguments[:index], value, *arguments[index + 1 :])


def same_value(a: object, b: object) -> bool:
    return type(a) is type(b) and a == b


def probe(
    db: AjeraOdbc, model: type[DatabaseRecord], report: Callable[[str], None]
) -> Probed:
    """Each parameter's evidence, by the codes it was probed under."""
    parameters = model.__source__.parameters
    values = plan(model)
    if values is None:
        report("no base arguments; unchecked")
        return Probed({name: {"": Evidence()} for name in parameters})
    base = tuple(value for value, _ in values.values())
    fingerprint = Fingerprints(db, model)
    fingerprint.settle(base)
    first = fingerprint(base)
    report(f"base rows={rows(first)}")
    if fingerprint.volatile:
        report(
            f"left out, moved between identical calls: {', '.join(fingerprint.volatile)}"
        )
    probed = Probed({name: {} for name in parameters})

    # A code that returns different rows is a context the others are probed
    # in again: it can change what the dates mean.
    contexts: dict[tuple[object, ...], list[object]] = {base: []}
    codes = [n for n in parameters if n in CODES]
    if len(codes) > 1:
        raise NotImplementedError(f"{model.__source__.name} has two code parameters")
    if codes:
        probed.code = code = codes[0]
        contexts[base].append(base[parameters.index(code)])
        evidence = probed.evidence[code].setdefault("", Evidence())
        for value in [*values[code][1], None]:
            other = replaced(parameters, base, code, value)
            compare(fingerprint, evidence, f"{value}", base, other)
            if not rows(fingerprint(other)):
                continue
            same = next(
                (c for c in contexts if fingerprint(c) == fingerprint(other)), None
            )
            contexts.setdefault(other if same is None else same, []).append(value)

    for context, equivalent in contexts.items():
        label = (
            f"{probed.code}={context[parameters.index(probed.code)]}"
            if probed.code
            else ""
        )
        probed.codes[label] = equivalent
        found = {
            n: probed.evidence[n].setdefault(label, Evidence())
            for n in parameters
            if n != probed.code
        }
        for name in (n for n in parameters if n != probed.code):
            current = context[parameters.index(name)]
            for value in [*values[name][1], None]:
                if found[name].changed:
                    break
                if not same_value(value, current):
                    other = replaced(parameters, context, name, value)
                    compare(fingerprint, found[name], f"{value}", context, other)
        if all(n in parameters and not found[n].changed for n in DATE_RANGE):
            other = context
            for name, value in zip(DATE_RANGE, OTHER_RANGE, strict=True):
                other = replaced(parameters, other, name, value)
            for name in DATE_RANGE:
                compare(
                    fingerprint,
                    found[name],
                    f"{OTHER_RANGE[0]}..{OTHER_RANGE[1]}",
                    context,
                    other,
                )

    if fingerprint(base, fresh=True) != first:
        # Every difference was confirmed on fresh calls, and an unchanged
        # result is never an edit's doing, so the verdicts stand.
        report("base result moved during the probe; each difference was confirmed")
    report(f"{fingerprint.calls} calls")
    return probed


def verdict(by_context: dict[str, Evidence]) -> str:
    """Applied if it changed the rows under any code, else as the evidence says."""
    evidence = Evidence(
        changed=[c for e in by_context.values() for c in e.changed],
        unchanged=[c for e in by_context.values() for c in e.unchanged],
        empty=[c for e in by_context.values() for c in e.empty],
    )
    return evidence.verdict


def verified_filters(
    db: AjeraOdbc, model: type[DatabaseRecord], ignored: Sequence[str]
) -> dict[str, Filter]:
    """The filters in `FILTERS` for these parameters that narrow the rows."""
    source = model.__source__
    arguments = base_arguments(model) or ()
    kept: dict[str, Filter] = {}
    rules = {n: r for n, r in FILTERS.get(source.name, {}).items() if n in ignored}
    total = db.count(model, *arguments) if rules else 0
    for name, rule in rules.items():
        narrowed = db.count(
            model,
            *arguments,
            where={rule.column: between(*RANGES.get(source.name, RANGE))},
        )
        if 0 < narrowed < total:
            kept[name] = rule
        else:
            print(f"    filter {rule.column} does not narrow the rows; not recorded")
    return kept


# =============================================================================
# Main
# =============================================================================


def record(
    function: dict[str, Any], key: str, value: Sequence[str] | dict[str, Any]
) -> None:
    if value:
        function[key] = value
    else:
        function.pop(key, None)


def ignored_when(probed: Probed, verdicts: dict[str, str]) -> dict[str, Any]:
    """The parameters applied under some codes but not under others."""
    when: dict[str, Any] = {}
    for name, verdict_ in verdicts.items():
        if probed.code is None or name == probed.code or verdict_ != "applied":
            continue
        under = [
            value
            for label, evidence in probed.evidence[name].items()
            if evidence.verdict == "no effect"
            for value in probed.codes[label]
        ]
        if under:
            when[name] = {probed.code: sorted(under, key=lambda v: (v is None, v))}
    return when


def main(names: Sequence[str]) -> int:
    # The probe passes values to ignored parameters on purpose.
    logging.getLogger("ajera.odbc.arguments").setLevel(logging.ERROR)
    chosen = [n for n in FUNCTIONS if not names or n in names]
    unknown = sorted(set(names) - set(FUNCTIONS))
    if unknown:
        print(f"unknown functions: {', '.join(unknown)}", file=sys.stderr)
        return 2

    with AjeraOdbc(timeout=(30, 240)) as db:
        add_live_values(db)
        for name in chosen:
            model = FUNCTIONS[name]
            parameters = model.__source__.parameters
            started = time.monotonic()
            print(name, flush=True)

            def report(line: str) -> None:
                print(f"  {line}", flush=True)

            if name in SLOW:
                report("too slow to probe; unchecked")
                probed = Probed({p: {"": Evidence()} for p in parameters})
            else:
                probed = probe(db, model, report)
            verdicts = {p: verdict(probed.evidence[p]) for p in parameters}
            for parameter in parameters:
                report(f"@{parameter}: {verdicts[parameter]}")
                for context, evidence in probed.evidence[parameter].items():
                    why = "; ".join(evidence.changed[:1])
                    if context or why:
                        codes = ", ".join(map(str, probed.codes.get(context, [])))
                        shown = f"{context} (also {codes})" if "," in codes else context
                        report(f"    {shown or 'base'}: {evidence.verdict} {why}")

            ignored = [p for p in parameters if verdicts[p] == "no effect"]
            filters = verified_filters(db, model, ignored)
            when = ignored_when(probed, verdicts)
            if when:
                report(f"ignored under some codes: {when}")
            # Read again before writing, so runs in parallel keep each other's.
            catalog = json.loads(CATALOG.read_text())
            function = catalog["functions"][name]
            record(function, "ignored_parameters", ignored)
            record(
                function,
                "unchecked_parameters",
                [p for p in parameters if verdicts[p] == "unchecked"],
            )
            record(
                function,
                "parameter_filters",
                {p: rule.column for p, rule in filters.items()},
            )
            record(
                function,
                "parameter_notes",
                {p: rule.note for p, rule in filters.items() if rule.note},
            )
            record(function, "ignored_when", when)
            CATALOG.write_text(dump(catalog))
            report(f"{time.monotonic() - started:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
