"""Render real PDFs, rasterize them and decode every barcode with ZXing (the decoder stock-count falls back to)."""

import pypdfium2 as pdfium
import pytest
import zxingcpp

from shelf_labels.data import Label
from shelf_labels.layouts import load_layouts
from shelf_labels.pdf import render_pdf

LAYOUTS = load_layouts()
CODES = ["A-01-01", "WIDGET-0042", "12345678", "loc/R2 S3", "x", "Q^Z~_9", "AB-1234-XY07"]
FORMAT = {"code128": zxingcpp.BarcodeFormat.Code128, "qr": zxingcpp.BarcodeFormat.QRCode}


def decode(path, dpi=300):
    pages = []
    for page in pdfium.PdfDocument(path):
        found = zxingcpp.read_barcodes(page.render(scale=dpi / 72).to_pil())
        pages.append(sorted((r.text, r.format) for r in found))
    return pages


@pytest.mark.parametrize("layout", ["avery-5160", "avery-5163", "avery-l7160", "zebra-2x1", "zebra-4x2"])
@pytest.mark.parametrize("symbology", ["code128", "qr"])
def test_every_label_scans_back_to_its_code(tmp_path, layout, symbology):
    out = tmp_path / "labels.pdf"
    labels = [Label(c, "Some description that is far too long to fit on one small label") for c in CODES]
    pages = render_pdf(labels, LAYOUTS[layout], out, symbology)
    decoded = decode(out)
    assert len(decoded) == pages
    assert sorted(item for page in decoded for item in page) == sorted((c, FORMAT[symbology]) for c in CODES)


def test_sheet_spills_onto_a_second_page(tmp_path):
    out = tmp_path / "labels.pdf"
    codes = [f"BIN-{i:03}" for i in range(31)]
    assert render_pdf([Label(c) for c in codes], LAYOUTS["avery-5160"], out) == 2
    first, second = decode(out)
    assert len(first) == 30 and second == [("BIN-030", zxingcpp.BarcodeFormat.Code128)]


def test_code_too_long_for_code128_is_refused_and_no_file_is_written(tmp_path):
    out = tmp_path / "labels.pdf"
    with pytest.raises(ValueError, match="use --barcode qr"):
        render_pdf([Label("A1"), Label("X" * 40)], LAYOUTS["avery-5160"], out)
    assert not out.exists()
    render_pdf([Label("X" * 64)], LAYOUTS["avery-5160"], out, "qr")  # QR takes the longest allowed code
    assert decode(out) == [[("X" * 64, zxingcpp.BarcodeFormat.QRCode)]]
