"""
Verify every generated database model against the live database.

For each table and view, streams every row through its model and checks
that any recorded version marker (`tIsCurrent`, `tIsDeleted`, ...) holds only
0 and 1; for each documented code column, compares the codes in use with the
documented ones; for each table-valued function, calls it with
representative arguments. Only
names, counts, and validation error types are printed, never row values.

    make odbc-verify                    # everything
    make odbc-verify ARGS="AxProject"   # sources whose name contains a string
    make odbc-verify ARGS="--kinds view,function"
    make odbc-verify ARGS="--max-rows 100000"  # a sample per source

Exit status is non-zero when any model fails to validate a row.
"""

import sys
import time
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from enum import IntEnum

from pydantic import ValidationError

from ajera.odbc import AjeraOdbc
from ajera.schemas.database import FUNCTIONS, TABLES, VIEWS, DatabaseRecord

TODAY = date.today()
YEAR_START = date(TODAY.year, 1, 1)


def arguments_for(db: AjeraOdbc, name: str) -> list[tuple[object, ...]]:
    """Representative argument sets for each function, in declaration order."""
    receipt = db.read(TABLES["AxReceipt"], limit=1)
    receipt_key = receipt[0].receipt_key if receipt else 0  # type: ignore[attr-defined]
    period = (YEAR_START, TODAY)
    by_name: dict[str, list[tuple[object, ...]]] = {
        "Ax1099Totals": [(Decimal(0), *period)],
        "AxCreditMemo": [(receipt_key,)],
        "AxFinancials": [(*period, False, "Accrual"), (*period, False, "Cash")],
        "AxFinancials_MC": [(*period, False, "Accrual", None)],
        "AxFinancials_MC_TrialBalance": [(*period, False, "Accrual", None)],
        "AxGLBalanceTotals": [(TODAY,)],
        "AxGLDTotals": [(t, *period) for t in (0, 1, 2)],
        "AxLedger": [(*period, False, "Accrual")],
        "AxTranTotals": [(t, *period) for t in (0, 1, 2)],
        "BankEntries": [(TODAY,)],
        "ClientInvoiceTotals": [(t, *period) for t in (0, 1, 2)],
        "ClientTotals": [(t, *period) for t in (0, 1, 2)],
        "EmployeeTotals": [(t, *period) for t in (0, 1, 2)],
        "GLFullAccountWithCutoff": [(TODAY,)],
        "ProjectTotals": [period],
        "ReceiptTotals": [(*period, None, None, False)],
        "RefundTotals": [(*period, None, None)],
        "VendorInvoiceTotals": [(t, *period) for t in (0, 1, 2)],
        "VendorTotals": [(t, *period) for t in (0, 1, 2)],
    }
    return by_name.get(name, [])


def describe(error: ValidationError) -> Counter[str]:
    found: Counter[str] = Counter()
    for item in error.errors(include_input=False, include_url=False):
        found[f"{'.'.join(map(str, item['loc']))}: {item['type']}"] += 1
    return found


def verify_rows(
    db: AjeraOdbc, model: type[DatabaseRecord], max_rows: int | None
) -> tuple[int, Counter[str]]:
    """Stream rows through the model (up to `max_rows`), collecting failures."""
    errors: Counter[str] = Counter()
    rows = 0
    columns = db._select_list(model, include_blobs=False)
    # A keyed view reads in key order, so a repeated key shows up as two
    # adjacent rows; that would make paging and `get` on it mislead.
    key = (
        model.__source__.primary_key[0]
        if model.__source__.kind == "view" and model.__source__.primary_key
        else None
    )
    previous: object = None
    repeats = 0
    # The reader's own paging, so sources over the pipeline's 500,000-row
    # limit are verified the way callers read them.
    for record in db._records_paged(
        model,
        columns,
        where=None,
        order_by=None,
        limit=max_rows,
        offset=None,
        batch_size=10000,
    ):
        rows += 1
        if key is not None:
            repeats += record[key] == previous
            previous = record[key]
        try:
            model.model_validate(record)
        except ValidationError as error:
            errors.update(describe(error))
    if repeats:
        errors[f"key {key} repeats {repeats} times"] += 1
    return rows, errors


def verify_blobs(db: AjeraOdbc, model: type[DatabaseRecord]) -> Counter[str]:
    errors: Counter[str] = Counter()
    if model.__source__.blobs:
        try:
            db.read(model, limit=5, include_blobs=True)
        except ValidationError as error:
            errors.update(describe(error))
    return errors


def verify_versioned(db: AjeraOdbc, model: type[DatabaseRecord]) -> Counter[str]:
    """The recorded current and deleted columns exist live and hold only 0 and 1."""
    errors: Counter[str] = Counter()
    source = model.__source__
    live = {name for name, _ in db.columns(model)}
    for column in (source.current_column, source.deleted_column):
        if column is None:
            continue
        if column not in live:
            errors[f"{column}: recorded as a version marker but not a live column"] += 1
            continue
        cursor = db.connection.cursor()
        try:
            cursor.execute(f"SELECT DISTINCT [{column}] FROM [dbo].[{source.name}]")
            values = {row[0] for row in cursor.fetchall()}
        finally:
            cursor.close()
        # True and False compare equal to 1 and 0, so only NULL or another
        # value is left over.
        if unexpected := values - {0, 1}:
            errors[
                f"{column}: holds {sorted(map(repr, unexpected))}, not only 0 and 1"
            ] += 1
    return errors


def verify_codes(db: AjeraOdbc, model: type[DatabaseRecord]) -> list[str]:
    """Codes in use that the documented enum does not name."""
    findings = []
    for field in model.model_fields.values():
        enum = next(
            (
                a
                for a in getattr(field.annotation, "__args__", ())
                if isinstance(a, type) and issubclass(a, IntEnum)
            ),
            None,
        )
        if enum is None or not field.alias:
            continue
        cursor = db.connection.cursor()
        try:
            cursor.execute(
                f"SELECT DISTINCT [{field.alias}] FROM [dbo].[{model.__source__.name}]"
            )
            used = {row[0] for row in cursor.fetchall() if row[0] is not None}
        finally:
            cursor.close()
        missing = sorted(code for code in used if code not in enum._value2member_map_)
        if missing:
            findings.append(
                f"{field.alias} uses undocumented {enum.__name__} codes {missing}"
            )
    return findings


def main(match: str, kinds: set[str], max_rows: int | None) -> int:
    failed = 0
    totals: Counter[str] = Counter()
    with AjeraOdbc(timeout=(30, 300)) as db:
        for group, models in (("table", TABLES), ("view", VIEWS)):
            if group not in kinds:
                continue
            for name, model in models.items():
                if match not in name:
                    continue
                start = time.monotonic()
                try:
                    rows, errors = verify_rows(db, model, max_rows)
                    errors.update(verify_blobs(db, model))
                    errors.update(verify_versioned(db, model))
                    codes = verify_codes(db, model) if group == "table" else []
                except Exception as error:  # noqa: BLE001 - report and continue
                    print(f"ERROR {group} {name}: {str(error)[:300]}")
                    failed += 1
                    continue
                totals[group] += rows
                status = "FAIL" if errors else "ok"
                failed += bool(errors)
                print(
                    f"{status:4} {group} {name}: {rows} rows in {time.monotonic() - start:.1f}s"
                )
                for problem, count in errors.most_common(10):
                    print(f"       {problem} x{count}")
                for finding in codes:
                    print(f"       note: {finding}")

        for name, model in FUNCTIONS.items() if "function" in kinds else ():
            if match not in name:
                continue
            for arguments in arguments_for(db, name):
                shown = ", ".join(
                    a.isoformat() if isinstance(a, (date, datetime)) else repr(a)
                    for a in arguments
                )
                start = time.monotonic()
                try:
                    rows = db.call(model, *arguments, limit=max_rows)
                    totals["function"] += len(rows)
                    print(
                        f"ok   function {name}({shown}): {len(rows)} rows in {time.monotonic() - start:.1f}s"
                    )
                except ValidationError as error:
                    failed += 1
                    print(f"FAIL function {name}({shown})")
                    for problem, count in describe(error).most_common(10):
                        print(f"       {problem} x{count}")
                except Exception as error:  # noqa: BLE001 - report and continue
                    failed += 1
                    print(f"ERROR function {name}({shown}): {str(error)[:300]}")

    print(f"verified rows: {dict(totals)}; failures: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    arguments = sys.argv[1:]
    kinds = {"table", "view", "function"}
    if "--kinds" in arguments:
        at = arguments.index("--kinds")
        kinds = set(arguments[at + 1].split(","))
        del arguments[at : at + 2]
    max_rows = None
    if "--max-rows" in arguments:
        at = arguments.index("--max-rows")
        max_rows = int(arguments[at + 1])
        del arguments[at : at + 2]
    sys.exit(main(arguments[0] if arguments else "", kinds, max_rows))
