"""ZPL II for Zebra thermal printers: one ^XA...^XZ block per label."""

from .barcodes import CODE128_QUIET, MIN_MODULE_MM, QR_QUIET, code128_modules_max, qr_modules, too_small
from .data import Label
from .layouts import Layout

PAD = 2.0  # mm


def escape(value: str) -> str:
    """Field data goes through ^FH_, so ^ ~ _ in a code or description cannot start a ZPL command."""
    return value.replace("_", "_5F").replace("^", "_5E").replace("~", "_7E")


def _field(x: int, y: int, body: str, value: str) -> str:
    return f"^FO{x},{y}{body}^FH_^FD{value}^FS"


def _label(label: Label, layout: Layout, symbology: str) -> str:
    dots = layout.dpi / 25.4  # per mm
    w, h, pad = round(layout.label_width * dots), round(layout.label_height * dots), round(PAD * dots)
    font = round(2.8 * dots)  # about 8 pt
    small = round(2.4 * dots)
    out = ["^XA", "^CI28", f"^PW{w}", f"^LL{h}"]
    if symbology == "code128":
        lines = 2 if label.text else 1
        space = w - 2 * pad
        module = space // (code128_modules_max(label.code) + 2 * CODE128_QUIET)
        if module / dots < MIN_MODULE_MM - 1e-9:
            raise too_small(label.code, "code128", module / dots, space / dots)
        bar_h = h - 2 * pad - lines * (font + 4)
        if bar_h < 5 * dots:
            raise ValueError(f"label is too short for a Code 128 barcode ({bar_h / dots:.1f} mm of bar height)")
        # ^BC mode A lets the printer pick code sets; the symbol is never wider than the bound above.
        out.append(f"^BY{module},3,{bar_h}")
        out.append(_field(pad + CODE128_QUIET * module, pad, f"^BCN,{bar_h},N,N,N,A", escape(label.code)))
        text_y = pad + bar_h + 4
        out.append(_field(pad, text_y, f"^A0N,{font},{font}^FB{space},1,0,C", escape(label.code)))
        if label.text:
            out.append(_field(pad, text_y + font + 4, f"^A0N,{small},{small}^FB{space},1,0,C", escape(label.text)))
    else:
        side = min(h - 2 * pad, (w - 2 * pad) // 2)
        mag = min(10, side // (qr_modules(label.code) + 2 * QR_QUIET))
        if mag / dots < MIN_MODULE_MM - 1e-9:
            raise too_small(label.code, "qr", mag / dots, side / dots)
        # ^BQ data starts with error level M and A for automatic input mode.
        out.append(_field(pad + QR_QUIET * mag, pad + QR_QUIET * mag, f"^BQN,2,{mag}", "MA," + escape(label.code)))
        text_x = pad + side + round(dots)
        text_w = w - pad - text_x
        mid = h // 2
        out.append(_field(text_x, mid - font - 2, f"^A0N,{font},{font}^FB{text_w},1,0,L", escape(label.code)))
        if label.text:
            out.append(_field(text_x, mid + 2, f"^A0N,{small},{small}^FB{text_w},1,0,L", escape(label.text)))
    out.append("^XZ")
    return "\n".join(out)


def render_zpl(labels: list[Label], layout: Layout, symbology: str = "code128") -> str:
    if layout.page:
        raise ValueError(f"layout {layout.name} is a sheet layout; ZPL needs a roll layout such as zebra-2x1")
    return "\n".join(_label(label, layout, symbology) for label in labels) + "\n"
