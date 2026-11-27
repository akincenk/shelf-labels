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


def test_warnings_summary_and_strict(tmp_path, capsys):
    csv = tmp_path / "in.csv"
    csv.write_text("sku,name\nA-01,x\nA-01,y\n,\n")
    out = tmp_path / "l.pdf"
    assert main(["pdf", str(csv), "-o", str(out), "--layout", "avery-5160"]) == 0
    cap = capsys.readouterr()
    assert "warning: " in cap.err and "line 3: code 'A-01' already on line 2" in cap.err
    assert "wrote 2 labels on 1 page(s)" in cap.out
    assert cap.out.strip().endswith(", 1 blank row(s) skipped, 1 duplicate code(s)")
    out.unlink()
    assert main(["zpl", str(csv), "-o", str(out), "--layout", "zebra-2x1", "--strict"]) == 1
    assert "2 warning(s) and --strict given, nothing written" in capsys.readouterr().err
    assert not out.exists()
    csv.write_text("sku\nA-01\n")
    assert main(["zpl", str(csv), "-o", str(out), "--layout", "zebra-2x1", "--strict"]) == 0
    assert capsys.readouterr().out.strip() == f"wrote 1 labels to {out}"
