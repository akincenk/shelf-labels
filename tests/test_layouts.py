import pytest

from shelf_labels.layouts import load_layouts


def test_builtin_layouts_fit_their_pages():
    layouts = load_layouts()
    assert {"avery-5160", "avery-5163", "avery-l7160", "zebra-2x1", "zebra-4x2"} <= set(layouts)
    assert layouts["avery-5160"].per_page == 30
    assert layouts["zebra-2x1"].per_page == 1


def test_user_file_adds_and_replaces(tmp_path):
    cfg = tmp_path / "labels.toml"
    cfg.write_text(
        "[bin-tag]\nlabel_width = 76.2\nlabel_height = 50.8\ndpi = 300\n[zebra-2x1]\nlabel_width = 50\nlabel_height = 30\n"
    )
    layouts = load_layouts(cfg)
    assert layouts["bin-tag"].dpi == 300
    assert layouts["zebra-2x1"].label_height == 30
    assert "avery-5160" in layouts


@pytest.mark.parametrize(
    "toml, message",
    [
        ("[x]\nlabel_width = 10\nlabel_height = 10\ncolour = 'red'\n", "unknown keys: colour"),
        ("[x]\nlabel_width = 10\n", "label_height"),
        ("[x]\nlabel_width = 0\nlabel_height = 10\n", "must be positive"),
        ("[x]\nlabel_width = 10\nlabel_height = 10\ndpi = 100\n", "dpi"),
        ("[x]\npage = 'legal'\nlabel_width = 10\nlabel_height = 10\n", "page must be"),
        ("[x]\npage = 'a4'\ncolumns = 4\nlabel_width = 60\nlabel_height = 10\n", "do not fit"),
        ("x = 1\n", "must be a table"),
        ("[x\n", "labels.toml"),
    ],
)
def test_bad_config(tmp_path, toml, message):
    cfg = tmp_path / "labels.toml"
    cfg.write_text(toml)
    with pytest.raises(ValueError, match=message):
        load_layouts(cfg)
