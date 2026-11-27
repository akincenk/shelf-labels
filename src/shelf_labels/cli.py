"""shelf-labels command line."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .barcodes import SYMBOLOGIES
from .data import read_labels
from .layouts import load_layouts
from .pdf import render_pdf
from .zpl import render_zpl


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="shelf-labels", description="Turn a CSV of SKUs or locations into labels.")
    p.add_argument("--version", action="version", version=f"shelf-labels {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    ls = sub.add_parser("layouts", help="list the available label layouts")
    ls.add_argument("--config", type=Path, help="TOML file with extra layouts")

    for name, what in (("pdf", "print-ready PDF"), ("zpl", "ZPL for Zebra printers")):
        s = sub.add_parser(name, help=f"write labels as {what}")
        s.add_argument("csv", type=Path, help="CSV file with a header row")
        s.add_argument("-o", "--output", type=Path, required=True, help="file to write")
        s.add_argument("--layout", required=True, help="layout name (see: shelf-labels layouts)")
        s.add_argument("--config", type=Path, help="TOML file with extra layouts")
        s.add_argument("--column", default="sku", help="CSV column holding the code (default: sku)")
        s.add_argument("--text-column", help="optional CSV column printed under the code, e.g. name")
        s.add_argument("--barcode", choices=SYMBOLOGIES, default="code128")
        s.add_argument("--strict", action="store_true", help="treat warnings (duplicate codes, blank rows) as errors")
    return p


def run(argv: list[str] | None = None) -> str:
    args = _parser().parse_args(argv)
    layouts = load_layouts(args.config)
    if args.command == "layouts":
        return "\n".join(
            f"{lay.name:14} {lay.label_width:g} x {lay.label_height:g} mm, "
            + (f"{lay.page} sheet of {lay.per_page}" if lay.page else f"roll, {lay.dpi} dpi")
            for lay in layouts.values()
        )
    if args.layout not in layouts:
        raise ValueError(f"unknown layout {args.layout!r}; available: {', '.join(layouts)}")
    layout = layouts[args.layout]
    warnings: list[str] = []
    labels = read_labels(args.csv, args.column, args.text_column, warnings)
    for w in warnings:
        print(f"shelf-labels: {'error' if args.strict else 'warning'}: {w}", file=sys.stderr)
    if warnings and args.strict:
        raise ValueError(f"{len(warnings)} warning(s) and --strict given, nothing written")
    skipped = sum(w.endswith("blank row skipped") for w in warnings)
    dupes = len(warnings) - skipped
    note = "".join(
        f", {n} {what}" for n, what in ((skipped, "blank row(s) skipped"), (dupes, "duplicate code(s)")) if n
    )
    if args.command == "pdf":
        pages = render_pdf(labels, layout, args.output, args.barcode)
        return f"wrote {len(labels)} labels on {pages} page(s) to {args.output}{note}"
    args.output.write_text(render_zpl(labels, layout, args.barcode), encoding="utf-8")
    return f"wrote {len(labels)} labels to {args.output}{note}"


def main(argv: list[str] | None = None) -> int:
    try:
        print(run(argv))
    except (ValueError, OSError) as e:
        print(f"shelf-labels: error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
