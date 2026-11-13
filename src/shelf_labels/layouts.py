"""Label geometry, read from TOML. Built-in layouts ship in layouts.toml; a user file can add or replace them."""

import tomllib
from dataclasses import dataclass, fields
from importlib.resources import files
from pathlib import Path

PAGES = {"letter": (215.9, 279.4), "a4": (210.0, 297.0)}  # width, height in mm


@dataclass(frozen=True)
class Layout:
    name: str
    label_width: float
    label_height: float
    page: str | None = None
    columns: int = 1
    rows: int = 1
    margin_left: float = 0.0
    margin_top: float = 0.0
    gap_x: float = 0.0
    gap_y: float = 0.0
    dpi: int = 203

    @property
    def per_page(self) -> int:
        return self.columns * self.rows if self.page else 1

    def check(self) -> None:
        if self.label_width <= 0 or self.label_height <= 0:
            raise ValueError(f"layout {self.name}: label size must be positive")
        if self.dpi not in (152, 203, 300, 600):
            raise ValueError(f"layout {self.name}: dpi must be 152, 203, 300 or 600")
        if self.page is None:
            return
        if self.page not in PAGES:
            raise ValueError(f"layout {self.name}: page must be one of {', '.join(PAGES)}")
        if self.columns < 1 or self.rows < 1 or min(self.margin_left, self.margin_top, self.gap_x, self.gap_y) < 0:
            raise ValueError(f"layout {self.name}: columns/rows must be >= 1 and margins/gaps >= 0")
        page_w, page_h = PAGES[self.page]
        used_w = self.margin_left + self.columns * self.label_width + (self.columns - 1) * self.gap_x
        used_h = self.margin_top + self.rows * self.label_height + (self.rows - 1) * self.gap_y
        if used_w > page_w + 0.01 or used_h > page_h + 0.01:
            raise ValueError(f"layout {self.name}: labels do not fit on a {self.page} page")


_ALLOWED = {f.name for f in fields(Layout)} - {"name"}


def _parse(text: str, source: str) -> dict[str, Layout]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"{source}: {e}") from None
    layouts = {}
    for name, table in data.items():
        if not isinstance(table, dict):
            raise ValueError(f"{source}: [{name}] must be a table")  # noqa: TRY004 (user config error)
        unknown = set(table) - _ALLOWED
        if unknown:
            raise ValueError(f"{source}: [{name}] has unknown keys: {', '.join(sorted(unknown))}")
        try:
            layout = Layout(name=name, **table)
        except TypeError as e:
            raise ValueError(f"{source}: [{name}]: {e}") from None
        layout.check()
        layouts[name] = layout
    return layouts


def load_layouts(config: Path | None = None) -> dict[str, Layout]:
    layouts = _parse(files("shelf_labels").joinpath("layouts.toml").read_text(), "built-in layouts")
    if config is not None:
        layouts.update(_parse(Path(config).read_text(encoding="utf-8"), str(config)))
    return layouts
