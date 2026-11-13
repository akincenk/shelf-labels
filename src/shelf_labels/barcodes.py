"""Barcode sizes in modules (the narrowest bar or QR square), shared by the PDF and ZPL writers."""

from reportlab.graphics.barcode import qrencoder
from reportlab.graphics.barcode.code128 import Code128

SYMBOLOGIES = ("code128", "qr")
MIN_MODULE_MM = 0.25  # thinner bars are hard to read for phone cameras and cheap scanners
CODE128_QUIET = 10  # modules of white space each side of a Code 128 symbol
QR_QUIET = 4


def code128_modules(code: str) -> int:
    """Exact width of the Code 128 symbol reportlab draws (it switches to code set C for digit runs)."""
    return int(Code128(code, barWidth=1, quiet=False).width)


def code128_modules_max(code: str) -> int:
    """Upper bound for any Code 128 encoder: start + one code-set-B symbol per char + check + stop."""
    return 11 * len(code) + 35


def qr_modules(code: str) -> int:
    qr = qrencoder.QRCode(None, qrencoder.QRErrorCorrectLevel.M)
    qr.addData(code)
    qr.make()
    return qr.getModuleCount()


def too_small(code: str, symbology: str, module_mm: float, space_mm: float) -> ValueError:
    hint = "use --barcode qr or a larger layout" if symbology == "code128" else "use a larger layout"
    return ValueError(
        f"{code!r} does not fit as {symbology}: modules would be {module_mm:.3f} mm "
        f"(minimum {MIN_MODULE_MM}) in {space_mm:.1f} mm; {hint}"
    )
