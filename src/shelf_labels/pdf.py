"""Print-ready PDF: a full sheet for sheet layouts, one label per page for roll layouts."""

from pathlib import Path

from reportlab.graphics.barcode.code128 import Code128
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from .barcodes import CODE128_QUIET, MIN_MODULE_MM, QR_QUIET, code128_modules, qr_modules, too_small
from .data import Label
from .layouts import PAGES, Layout

PAD = 2.0  # mm inside each label edge; sheet labels are often cut slightly off
FONT = "Helvetica"
CODE_PT = 8
TEXT_PT = 7
LINE = 3.2  # mm per text line


def _fit(text: str, size: float, width_mm: float) -> str:
    """Cut text to fit width_mm, marking the cut with '...'."""
    if stringWidth(text, FONT, size) <= width_mm * mm:
        return text
    while text and stringWidth(text + "...", FONT, size) > width_mm * mm:
        text = text[:-1]
    return text + "..."


def _draw_code128(c: Canvas, label: Label, x: float, y: float, w: float, h: float) -> None:
    lines = 2 if label.text else 1
    bar_h = h - 2 * PAD - lines * LINE
    space = w - 2 * PAD
    module = space / (code128_modules(label.code) + 2 * CODE128_QUIET)
    if module < MIN_MODULE_MM:
        raise too_small(label.code, "code128", module, space)
    if bar_h < 5:
        raise ValueError(f"label is too short for a Code 128 barcode ({bar_h:.1f} mm of bar height)")
    bc = Code128(label.code, barWidth=module * mm, barHeight=bar_h * mm, quiet=False)
    bc.drawOn(c, (x + (w - bc.width / mm) / 2) * mm, (y + PAD + lines * LINE) * mm)
    c.setFont(FONT, CODE_PT)
    c.drawCentredString((x + w / 2) * mm, (y + PAD + (lines - 1) * LINE + 0.6) * mm, label.code)
    if label.text:
        c.setFont(FONT, TEXT_PT)
        c.drawCentredString((x + w / 2) * mm, (y + PAD + 0.6) * mm, _fit(label.text, TEXT_PT, space))


def _draw_qr(c: Canvas, label: Label, x: float, y: float, w: float, h: float) -> None:
    side = min(h - 2 * PAD, (w - 2 * PAD) / 2)
    modules = qr_modules(label.code) + 2 * QR_QUIET
    if side / modules < MIN_MODULE_MM:
        raise too_small(label.code, "qr", side / modules, side)
    widget = QrCodeWidget(label.code, barLevel="M", barBorder=QR_QUIET, barWidth=side * mm, barHeight=side * mm)
    d = Drawing(side * mm, side * mm)
    d.add(widget)
    d.drawOn(c, (x + PAD) * mm, (y + (h - side) / 2) * mm)
    text_x = x + PAD + side + 1
    text_w = x + w - PAD - text_x
    mid = y + h / 2
    c.setFont(FONT, CODE_PT)
    c.drawString(text_x * mm, (mid + (0.3 if label.text else -1)) * mm, _fit(label.code, CODE_PT, text_w))
    if label.text:
        c.setFont(FONT, TEXT_PT)
        c.drawString(text_x * mm, (mid - LINE) * mm, _fit(label.text, TEXT_PT, text_w))


def _positions(layout: Layout):
    """Bottom-left corner (mm, PDF coordinates) of each label slot on a page, in reading order."""
    if layout.page is None:
        return [(0.0, 0.0)]
    page_h = PAGES[layout.page][1]
    return [
        (
            layout.margin_left + col * (layout.label_width + layout.gap_x),
            page_h - layout.margin_top - (row + 1) * layout.label_height - row * layout.gap_y,
        )
        for row in range(layout.rows)
        for col in range(layout.columns)
    ]


def render_pdf(labels: list[Label], layout: Layout, out: Path, symbology: str = "code128") -> int:
    """Write the PDF and return the number of pages."""
    draw = {"code128": _draw_code128, "qr": _draw_qr}[symbology]
    if layout.page:
        size = tuple(v * mm for v in PAGES[layout.page])
    else:
        size = (layout.label_width * mm, layout.label_height * mm)
    slots = _positions(layout)
    # reportlab writes the file only in save(), so a label that does not fit leaves no partial PDF.
    c = Canvas(str(out), pagesize=size, pageCompression=1)
    c.setTitle("shelf-labels")
    pages = 0
    for start in range(0, len(labels), len(slots)):
        for label, (x, y) in zip(labels[start : start + len(slots)], slots):
            draw(c, label, x, y, layout.label_width, layout.label_height)
        c.showPage()
        pages += 1
    c.save()
    return pages
