"""Read label rows from CSV and validate the codes that go into barcodes."""

import csv
from dataclasses import dataclass
from pathlib import Path

MAX_CODE = 64  # stock-count and Warehouse-inventory-api accept SKU codes of 1-64 characters


@dataclass(frozen=True)
class Label:
    code: str
    text: str = ""


def check_code(code: str) -> str:
    """Codes must survive Code 128, ZPL and a phone scan unchanged: printable ASCII, no edge spaces."""
    if not 1 <= len(code) <= MAX_CODE:
        raise ValueError(f"code must be 1-{MAX_CODE} characters, got {len(code)}")
    if code != code.strip():
        raise ValueError(f"code {code!r} has leading or trailing spaces")
    bad = [c for c in code if not " " <= c <= "~"]
    if bad:
        raise ValueError(f"code {code!r} has characters outside printable ASCII: {bad[0]!r}")
    return code


def read_labels(path: Path, code_column: str = "sku", text_column: str | None = None) -> list[Label]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        for col in filter(None, (code_column, text_column)):
            if col not in headers:
                raise ValueError(f"{path}: no column {col!r}; columns are: {', '.join(headers)}")
        labels = []
        for row in reader:
            code = (row[code_column] or "").strip()
            try:
                check_code(code)
            except ValueError as e:
                raise ValueError(f"{path}, line {reader.line_num}: {e}") from None
            text = (row[text_column] or "").strip() if text_column else ""
            labels.append(Label(code, text))
    if not labels:
        raise ValueError(f"{path}: no rows")
    return labels
