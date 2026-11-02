"""
Extract the documented enum codes from Deltek's Ajera schema workbook.

The workbook comes from Ajera itself (Setup > Utility > Ajera Schema) and is
the only place the meaning of each `tinyint` code column is written down. Its
`Enum Values` cell reads like `0 = Inactive; 1 = Active`. Run with openpyxl:

    make odbc-enums XLSX=path/to/AjeraSchema.xlsx

Cells are capped at 255 characters in the export, so a long list can lose its
last entries; those are flagged `truncated` and the generator says so.
"""

import json
import re
import sys
from pathlib import Path

import openpyxl

PAIR = re.compile(r"\s*(-?\d+)\s*=\s*([^;]*)")
CELL_LIMIT = 255


def main(workbook: str, path: str) -> None:
    sheet = openpyxl.load_workbook(workbook, read_only=True).worksheets[0]
    enums: dict[str, dict[str, object]] = {}

    for table, column, _type, _nullable, _read_only, text in sheet.iter_rows(
        min_row=2, values_only=True
    ):
        if not (table and column and text):
            continue
        codes = {int(code): label.strip() for code, label in PAIR.findall(str(text))}
        codes = {code: label for code, label in codes.items() if label}
        if codes:
            enums[str(column)] = {
                "table": str(table),
                "codes": {str(code): label for code, label in sorted(codes.items())},
                "truncated": len(str(text)) >= CELL_LIMIT,
            }

    Path(path).write_text(json.dumps(enums, indent=1, sort_keys=True) + "\n")
    print(f"{path}: {len(enums)} enum columns")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "scripts/odbc/enums.json")
