"""
Snapshot the Ajera database catalog for the schema generator.

Reads only metadata (INFORMATION_SCHEMA and the sys catalog views), never
rows. Run it in the ODBC image with the `AJERA_ODBC_*` variables set:

    make odbc-catalog

The snapshot is tenant-neutral. Columns a tenant added as custom fields (the
`prj_MyField` shape: a lowercase prefix and an underscore) are dropped, as
are SQL Server's own tables, so the committed file describes the schema every
Ajera database shares. Custom fields still reach callers at run time through
`DatabaseRecord.custom_fields`.

What `probe.py` recorded about each function's parameters is carried over
from the existing snapshot, for the parameters the function still declares.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

from ajera.odbc import AjeraOdbc

CUSTOM_COLUMN = re.compile(r"^[a-z]+_")
SYSTEM_TABLES = {"dtproperties", "sysdiagrams"}
# Written by probe.py, not read from the catalog.
PROBED = (
    "ignored_parameters",
    "unchecked_parameters",
    "parameter_filters",
    "parameter_notes",
    "ignored_when",
)


def fetch(cursor: Any, statement: str) -> list[dict[str, Any]]:
    cursor.execute(statement)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def column(row: dict[str, Any]) -> dict[str, Any]:
    entry = {
        "name": row["COLUMN_NAME"],
        "type": row["DATA_TYPE"],
        "nullable": row["IS_NULLABLE"] == "YES",
    }
    for key, source in (
        ("length", "CHARACTER_MAXIMUM_LENGTH"),
        ("precision", "NUMERIC_PRECISION"),
        ("scale", "NUMERIC_SCALE"),
    ):
        if row.get(source) is not None and row["DATA_TYPE"] in (
            ("decimal", "numeric")
            if key != "length"
            else ("varchar", "nvarchar", "char", "nchar", "varbinary")
        ):
            entry[key] = int(row[source])
    if row.get("IS_IDENTITY") == 1:
        entry["identity"] = True
    if row.get("IS_COMPUTED") == 1:
        entry["computed"] = True
    return entry


def dump(catalog: dict[str, dict[str, Any]]) -> str:
    """Write one column per line, so a schema change reads as a small diff."""
    lines = ["{"]
    for g, (group, sources) in enumerate(catalog.items()):
        lines.append(f'  "{group}": {{')
        for s, (name, source) in enumerate(sources.items()):
            lines.append(f'    "{name}": {{')
            for k, (key, value) in enumerate(source.items()):
                comma = "," if k < len(source) - 1 else ""
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    lines.append(f'      "{key}": [')
                    lines += [
                        f"        {json.dumps(item)}{',' if i < len(value) - 1 else ''}"
                        for i, item in enumerate(value)
                    ]
                    lines.append(f"      ]{comma}")
                else:
                    lines.append(f'      "{key}": {json.dumps(value)}{comma}')
            lines.append(f"    }}{',' if s < len(sources) - 1 else ''}")
        lines.append(f"  }}{',' if g < len(catalog) - 1 else ''}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def carry_probed(catalog: dict[str, dict[str, Any]], path: Path) -> None:
    """Keep what probe.py found, for parameters each function still declares."""
    if not path.exists():
        return
    previous = json.loads(path.read_text()).get("functions", {})
    for name, function in catalog["functions"].items():
        declared = {parameter["name"] for parameter in function["parameters"]}
        for key in PROBED:
            value = previous.get(name, {}).get(key)
            if isinstance(value, dict):
                value = {k: v for k, v in value.items() if k in declared}
            elif isinstance(value, list):
                value = [v for v in value if v in declared]
            if value:
                function[key] = value


def main(path: str) -> None:
    with AjeraOdbc(timeout=(30, 600)) as db:
        cursor = db.connection.cursor()

        sources = fetch(
            cursor,
            "SELECT TABLE_NAME, TABLE_TYPE FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = 'dbo'",
        )
        columns = fetch(
            cursor,
            """
            SELECT TABLE_NAME, COLUMN_NAME, ORDINAL_POSITION, IS_NULLABLE, DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE,
                COLUMNPROPERTY(OBJECT_ID(QUOTENAME(TABLE_SCHEMA) + '.' + QUOTENAME(TABLE_NAME)),
                    COLUMN_NAME, 'IsIdentity') AS IS_IDENTITY,
                COLUMNPROPERTY(OBJECT_ID(QUOTENAME(TABLE_SCHEMA) + '.' + QUOTENAME(TABLE_NAME)),
                    COLUMN_NAME, 'IsComputed') AS IS_COMPUTED
            FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'dbo'
            ORDER BY TABLE_NAME, ORDINAL_POSITION
            """,
        )
        primary_keys = fetch(
            cursor,
            """
            SELECT tc.TABLE_NAME, kcu.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME AND tc.TABLE_NAME = kcu.TABLE_NAME
            WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
            ORDER BY tc.TABLE_NAME, kcu.ORDINAL_POSITION
            """,
        )
        foreign_keys = fetch(
            cursor,
            """
            SELECT OBJECT_NAME(fkc.parent_object_id) AS TABLE_NAME,
                COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS COLUMN_NAME,
                OBJECT_NAME(fkc.referenced_object_id) AS REF_TABLE,
                COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS REF_COLUMN
            FROM sys.foreign_key_columns fkc
            """,
        )
        parameters = fetch(
            cursor,
            """
            SELECT SPECIFIC_NAME, PARAMETER_NAME, ORDINAL_POSITION, DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE
            FROM INFORMATION_SCHEMA.PARAMETERS
            WHERE SPECIFIC_SCHEMA = 'dbo' AND PARAMETER_NAME <> ''
            ORDER BY SPECIFIC_NAME, ORDINAL_POSITION
            """,
        )
        routine_columns = fetch(
            cursor,
            """
            SELECT TABLE_NAME, COLUMN_NAME, ORDINAL_POSITION, IS_NULLABLE, DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE
            FROM INFORMATION_SCHEMA.ROUTINE_COLUMNS WHERE TABLE_SCHEMA = 'dbo'
            ORDER BY TABLE_NAME, ORDINAL_POSITION
            """,
        )
        routines = fetch(
            cursor,
            "SELECT ROUTINE_NAME FROM INFORMATION_SCHEMA.ROUTINES "
            "WHERE ROUTINE_SCHEMA = 'dbo' AND ROUTINE_TYPE = 'FUNCTION' AND DATA_TYPE = 'TABLE'",
        )

    kinds = {row["TABLE_NAME"]: row["TABLE_TYPE"] for row in sources}
    catalog: dict[str, dict[str, Any]] = {"tables": {}, "views": {}, "functions": {}}

    for name, kind in sorted(kinds.items()):
        if name in SYSTEM_TABLES:
            continue
        group = "tables" if kind == "BASE TABLE" else "views"
        catalog[group][name] = {"columns": []}

    for row in columns:
        entry = catalog["tables"].get(row["TABLE_NAME"]) or catalog["views"].get(
            row["TABLE_NAME"]
        )
        if entry is not None and not CUSTOM_COLUMN.match(row["COLUMN_NAME"]):
            entry["columns"].append(column(row))

    for row in primary_keys:
        table = catalog["tables"].get(row["TABLE_NAME"])
        if table is not None:
            table.setdefault("primary_key", []).append(row["COLUMN_NAME"])

    for row in sorted(foreign_keys, key=lambda r: (r["TABLE_NAME"], r["COLUMN_NAME"])):
        table = catalog["tables"].get(row["TABLE_NAME"])
        if table is not None and not CUSTOM_COLUMN.match(row["COLUMN_NAME"]):
            table.setdefault("foreign_keys", {})[row["COLUMN_NAME"]] = [
                row["REF_TABLE"],
                row["REF_COLUMN"],
            ]

    for row in sorted(routines, key=lambda r: r["ROUTINE_NAME"]):
        catalog["functions"][row["ROUTINE_NAME"]] = {"parameters": [], "columns": []}
    for row in parameters:
        function = catalog["functions"].get(row["SPECIFIC_NAME"])
        if function is not None:
            parameter = column(
                {
                    **row,
                    "COLUMN_NAME": row["PARAMETER_NAME"].lstrip("@"),
                    "IS_NULLABLE": "YES",
                }
            )
            del parameter["nullable"]
            function["parameters"].append(parameter)
    for row in routine_columns:
        function = catalog["functions"].get(row["TABLE_NAME"])
        if function is not None and not CUSTOM_COLUMN.match(row["COLUMN_NAME"]):
            function["columns"].append(column(row))

    carry_probed(catalog, Path(path))
    Path(path).write_text(dump(catalog))
    print(
        f"{path}: {len(catalog['tables'])} tables, {len(catalog['views'])} views, "
        f"{len(catalog['functions'])} functions"
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "scripts/odbc/catalog.json")
