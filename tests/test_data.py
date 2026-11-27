import pytest

from shelf_labels.data import Label, check_code, read_labels


def write(tmp_path, text, name="in.csv"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_reads_codes_and_text_and_strips_spaces(tmp_path):
    p = write(tmp_path, "﻿sku,name\n A-01 ,Shelf A\nB-02,\n")
    assert read_labels(p, text_column="name") == [Label("A-01", "Shelf A"), Label("B-02", "")]


def test_other_code_column(tmp_path):
    p = write(tmp_path, "location,zone\nR1-S2,cold\n")
    assert read_labels(p, "location") == [Label("R1-S2")]


def test_missing_column_lists_headers(tmp_path):
    p = write(tmp_path, "code,name\nX,Y\n")
    with pytest.raises(ValueError, match="no column 'sku'; columns are: code, name"):
        read_labels(p)


def test_bad_code_reports_line(tmp_path):
    p = write(tmp_path, "sku\nOK-1\néclair\n")
    with pytest.raises(ValueError, match="line 3"):
        read_labels(p)


def test_empty_code_and_empty_file(tmp_path):
    with pytest.raises(ValueError, match="line 2: code must be 1-64"):
        read_labels(write(tmp_path, "sku,name\n,no code\n"))
    with pytest.raises(ValueError, match="no rows"):
        read_labels(write(tmp_path, "sku\n"))


@pytest.mark.parametrize("code", ["x" * 65, " A", "A\t", "A\nB", "café"])
def test_check_code_rejects(code):
    with pytest.raises(ValueError):
        check_code(code)


@pytest.mark.parametrize("code", ["A", "x" * 64, "A-01/02 B", "^XZ~_"])
def test_check_code_accepts(code):
    assert check_code(code) == code


def test_blank_rows_skipped_and_duplicates_reported(tmp_path):
    p = write(tmp_path, "sku,name\nA-01,x\n,\n , \nB-02,y\nA-01,again\n,,extra\n")
    warnings = []
    with pytest.raises(ValueError, match="line 7: code must be 1-64"):
        read_labels(p, warnings=warnings)
    p = write(tmp_path, "sku,name\nA-01,x\n,\n , \nB-02,y\nA-01,again\n")
    warnings = []
    assert read_labels(p, warnings=warnings) == [Label("A-01"), Label("B-02"), Label("A-01")]
    assert warnings == [
        f"{p}, line 3: blank row skipped",
        f"{p}, line 4: blank row skipped",
        f"{p}, line 6: code 'A-01' already on line 2",
    ]
    assert read_labels(p) == [Label("A-01"), Label("B-02"), Label("A-01")]  # no list given: still works
