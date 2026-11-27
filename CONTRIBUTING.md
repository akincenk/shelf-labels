# Contributing

Thanks for looking at shelf-labels. Issues and pull requests are welcome.

## Set up

You need Python 3.11 or newer.

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
```

## Before you open a pull request

```sh
ruff check . && ruff format --check .
pytest -q
gitleaks dir .
```

CI runs the same checks on Python 3.11 and 3.13, plus a gitleaks scan of the history and zizmor on the workflows.

## Guidelines

- One change per pull request, with tests. Bug fixes start with a test that fails.
- A label is only correct if it scans. PDF tests rasterize the page with pypdfium2 and decode it with zxing-cpp; keep that check for any change to drawing, sizes or layouts.
- Every text field in ZPL goes through `^FH` escaping in `zpl.py`. Codes and descriptions come from a CSV and are untrusted, so never write them into ZPL any other way.
- Codes stay within the rules in `data.check_code` (1 to 64 printable ASCII characters), the same rules stock-count and Warehouse-inventory-api use.
- No new runtime dependency without a good reason; the tool has one (reportlab).
- Sample SKUs, names and locations must be made up.
- The planned work is in [ROADMAP.md](ROADMAP.md); each item has a GitHub issue. Comment on the issue before starting a large item.
