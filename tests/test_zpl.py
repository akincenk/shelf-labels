import re

import pytest

from shelf_labels.data import Label
from shelf_labels.layouts import Layout, load_layouts
from shelf_labels.zpl import escape, render_zpl

ROLL = load_layouts()["zebra-2x1"]


def test_escape_blocks_command_injection():
    assert escape("A^XZ~JR_1") == "A_5EXZ_7EJR_5F1"


def test_one_block_per_label_with_size_in_dots():
    zpl = render_zpl([Label("A-01", "Shelf A"), Label("B-02")], ROLL)
    assert zpl.count("^XA") == zpl.count("^XZ") == 2
    assert "^PW406" in zpl and "^LL203" in zpl  # 2 x 1 in at 203 dpi
    assert "^BCN," in zpl and "^FH_^FDA-01^FS" in zpl and "^FDShelf A^FS" in zpl


def test_hostile_text_stays_inside_its_field():
    zpl = render_zpl([Label("A^B", "^XZ^XA~JR")], ROLL)
    assert zpl.count("^XA") == zpl.count("^XZ") == 1
    assert "~" not in zpl
    for data in re.findall(r"\^FD(.*?)\^FS", zpl):
        assert "^" not in data


def test_dpi_scales_bars():
    big = Layout("hi", 50.8, 25.4, dpi=300)
    module = int(re.search(r"\^BY(\d+)", render_zpl([Label("A-01")], big)).group(1))
    assert module * 25.4 / 300 >= 0.25


def test_qr():
    zpl = render_zpl([Label("WIDGET-0042", "Blue widget")], ROLL, "qr")
    assert re.search(r"\^BQN,2,\d+\^FH_\^FDMA,WIDGET-0042\^FS", zpl)


def test_refusals():
    with pytest.raises(ValueError, match="sheet layout"):
        render_zpl([Label("A")], load_layouts()["avery-5160"])
    with pytest.raises(ValueError, match="does not fit"):
        render_zpl([Label("X" * 20)], ROLL)
