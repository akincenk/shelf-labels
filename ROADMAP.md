# Roadmap

Planned work after the first version, roughly in order. Estimates are for one person and include tests and docs. Total: about 33 hours.

## 1. Labels straight from Warehouse-inventory-api (4 h)

`shelf-labels pdf --from-api URL` reads `GET /api/v1/skus` (code and name) with the key from the `INVENTORY_API_KEY` environment variable, so labels always match the database. Never print or log the key. Codes the API allows but labels cannot carry (non-ASCII) are listed and skipped with a clear message. Tests against a stub HTTP server.

## 2. Copies per row (1.5 h)

`--copies-column qty` prints each row that many times, for labelling every unit of a product. Reject negative or non-integer values with the CSV line number; cap at a sane maximum per run.

## 3. Start on a partly used sheet (1.5 h)

`--skip N` leaves the first N slots empty so a half-used sheet of labels can go back into the printer. Error if N is not smaller than the slots on a page.

## 4. Unicode descriptions in the PDF (3 h)

The built-in Helvetica font only covers Latin-1, so names in Turkish, Polish or Chinese print as boxes. Add `--font path.ttf` to register a TrueType font for the description line, and check ZPL with `^CI28` and a downloaded font. Codes stay ASCII.

## 5. Data Matrix symbology (3 h)

Data Matrix fits on very small bin labels where Code 128 is too wide. Add `--barcode datamatrix` for PDF (reportlab has an ECC200 encoder) and ZPL (`^BX`). Extend the scan-back tests; check that BarcodeDetector and the ZXing fallback in stock-count read it.

## 6. Exact Code 128 width in ZPL (2.5 h)

ZPL output uses an upper bound for the barcode width (one code set B symbol per character), so a long all-digit code is refused even though the printer would pack it with code set C. Compute the real width the way the printer's automatic mode does and keep a test that compares it with the Labelary render.

## 7. Better ZPL placement and golden tests (2 h)

Centre the QR code vertically, account for the `^BQ` top offset, and add stored reference renders for 203 and 300 dpi so layout changes are visible in review.

## 8. Location labels (3 h)

A label style for aisles and rack beams: the location code in large type, optional up or down arrow pointing at the shelf, barcode underneath. Chosen with `--style location`.

## 9. Calibration page and offsets (2 h)

`shelf-labels calibrate --layout NAME` prints the label outlines and a ruler so a user can see how far their printer shifts the sheet, then `--offset-x / --offset-y` in mm corrects it. Offsets can also be stored per layout in the TOML file.

## 10. Duplicate and summary report (1 h)

Warn when the same code appears twice in the CSV, and print a short summary (labels, pages, skipped rows). `--strict` turns warnings into errors.

## 11. Text templates (3 h)

Let a layout or the command line define the text lines from any CSV columns, for example `--line "{name}" --line "Bin {bin}  Zone {zone}"`. Missing columns are reported before anything is drawn.

## 12. Real printer and phone checks (1.5 h)

Print a test sheet on an office laser printer and a roll on a Zebra printer, scan both with stock-count on Android Chrome (BarcodeDetector) and iPhone Safari (ZXing fallback), and write the results in the README. Adjust the minimum bar width if needed.

## 13. More layouts (1.5 h)

Add common sizes: Avery 5167, 5195, L7651, L7163 and Zebra 3 x 1 and 4 x 6, each covered by the fit check and the scan-back test.

## 14. Pipes (1.5 h)

Read the CSV from stdin (`-`) and write ZPL to stdout (`-o -`) so the tool can sit in a shell pipeline, for example straight into `nc printer 9100`.

## 15. Release (2 h)

Tag v0.1.0, add a changelog, and publish to PyPI from GitHub Actions with trusted publishing (no API token stored in the repo).
