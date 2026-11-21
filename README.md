# shelf-labels

[![CI](https://github.com/akincenk/shelf-labels/actions/workflows/ci.yml/badge.svg)](https://github.com/akincenk/shelf-labels/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/akincenk/shelf-labels/badge)](https://scorecard.dev/viewer/?uri=github.com/akincenk/shelf-labels)

Turn a CSV of SKUs or shelf locations into barcode labels: Code 128 or QR, as a print-ready PDF for office label sheets (Avery and similar) or as ZPL for Zebra thermal printers.

It is meant for small warehouses and stockrooms that need to label bins, shelves and products without a label design program. The labels are made to be scanned by [stock-count](https://github.com/akincenk/stock-count), a phone app for cycle counts that syncs to [Warehouse-inventory-api](https://github.com/akincenk/Warehouse-inventory-api), but any Code 128 or QR scanner reads them.

## Stack

- Python 3.11+, one runtime dependency: [reportlab](https://www.reportlab.com/) for the PDF, Code 128 and QR drawing
- ZPL is written directly as text
- Layouts are TOML (read with the standard library `tomllib`)
- Tests: pytest. The PDF tests rasterize each page with pypdfium2 and decode every barcode with zxing-cpp, so a test only passes if the label actually scans back to its code.

## Install

```sh
git clone https://github.com/akincenk/shelf-labels
cd shelf-labels
python3 -m venv .venv && . .venv/bin/activate
pip install -e .            # add '.[dev]' to run the tests
```

## Use

Input is a CSV with a header row. By default the code is read from a column named `sku`:

```csv
sku,name
A-01-01,Aisle A bay 1 shelf 1
WIDGET-0042,Blue widget 40 mm
```

```sh
shelf-labels layouts
shelf-labels pdf examples/locations.csv -o labels.pdf --layout avery-5160 --text-column name
shelf-labels pdf examples/locations.csv -o labels.pdf --layout avery-l7160 --barcode qr
shelf-labels zpl examples/locations.csv -o labels.zpl --layout zebra-2x1 --text-column name
```

Options for `pdf` and `zpl`:

| Option | Meaning |
| --- | --- |
| `--layout NAME` | label geometry, see `shelf-labels layouts` |
| `--column NAME` | CSV column with the code (default `sku`) |
| `--text-column NAME` | optional column printed as a second line, cut with `...` if too long |
| `--barcode code128\|qr` | symbology (default `code128`) |
| `--config FILE` | TOML file with your own layouts |

Send a ZPL file to a networked Zebra printer with, for example, `nc printer-host 9100 < labels.zpl`.

When printing a PDF on label sheets, print at 100% ("actual size"), not "fit to page".

## Layouts

Built-in layouts (millimetres):

| Name | Label | Use |
| --- | --- | --- |
| `avery-5160` | 66.7 x 25.4 | US Letter sheet, 3 x 10 |
| `avery-5163` | 101.6 x 50.8 | US Letter sheet, 2 x 5 |
| `avery-l7160` | 63.5 x 38.1 | A4 sheet, 3 x 7 |
| `zebra-2x1` | 50.8 x 25.4 | thermal roll, 203 dpi |
| `zebra-4x2` | 101.6 x 50.8 | thermal roll, 203 dpi |

Add your own in a TOML file and pass it with `--config`. A table with `page` is a sheet; without `page` it is a roll label (one label per PDF page, and the size used for ZPL):

```toml
[bin-tag]
label_width = 76.2
label_height = 50.8
dpi = 300

[my-sheet]
page = "a4"        # letter or a4
columns = 2
rows = 8
label_width = 99.1
label_height = 33.9
margin_left = 4.65
margin_top = 12.9
gap_x = 2.5
gap_y = 0
```

## Rules the codes follow

- 1 to 64 characters, printable ASCII, no leading or trailing spaces. This matches what stock-count and Warehouse-inventory-api accept, and avoids characters that scan differently on different devices.
- A Code 128 bar is never thinner than 0.25 mm. If a code is too long for the label, the tool stops with an error that names the code instead of printing a label that will not scan. QR fits much longer codes on the same label.
- In ZPL, every field goes through `^FH`, so `^`, `~` and `_` in a code or description are printed as text and cannot act as printer commands.

## What has been checked

- PDF: every built-in layout, both symbologies, decoded back by zxing-cpp at 300 dpi in the test suite.
- ZPL: the output was rendered once with the Labelary online ZPL viewer and decoded with zxing-cpp (Code 128, QR, and a code containing `^ ~ _`). It has not been printed on a physical Zebra printer yet.
- Scanning the printed labels with stock-count on a phone has not been tested yet.

## Development

```sh
pip install -e '.[dev]'
ruff check . && ruff format --check .
pytest -q
```

See [ROADMAP.md](ROADMAP.md) for planned work.

## License

MIT, see [LICENSE](LICENSE).
