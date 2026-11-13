from shelf_labels.cli import main


def test_pdf_and_zpl_end_to_end(tmp_path, capsys):
    csv = tmp_path / "in.csv"
    csv.write_text("sku,name\nA-01,Shelf A\nB-02,Shelf B\n")
    assert (
        main(["pdf", str(csv), "-o", str(tmp_path / "l.pdf"), "--layout", "avery-5160", "--text-column", "name"]) == 0
    )
    assert (tmp_path / "l.pdf").read_bytes().startswith(b"%PDF")
    assert main(["zpl", str(csv), "-o", str(tmp_path / "l.zpl"), "--layout", "zebra-2x1", "--barcode", "qr"]) == 0
    assert (tmp_path / "l.zpl").read_text().count("^XA") == 2
    assert "wrote 2 labels" in capsys.readouterr().out


def test_errors_are_one_line_and_exit_1(tmp_path, capsys):
    csv = tmp_path / "in.csv"
    csv.write_text("sku\nA\n")
    assert main(["pdf", str(csv), "-o", str(tmp_path / "x.pdf"), "--layout", "nope"]) == 1
    assert "unknown layout 'nope'" in capsys.readouterr().err
    assert main(["pdf", str(tmp_path / "missing.csv"), "-o", "x.pdf", "--layout", "avery-5160"]) == 1
    assert "No such file" in capsys.readouterr().err


def test_layouts_lists_builtins(capsys):
    assert main(["layouts"]) == 0
    assert "avery-5160" in capsys.readouterr().out
