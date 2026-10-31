import runpy
from pathlib import Path

import pytest
from PIL import Image

from haylou_tools import tbwf
from haylou_tools.cli import main

ROOT = Path(__file__).parent.parent


@pytest.fixture
def face(tmp_path, font):
    path = tmp_path / "f.tbwf"
    tbwf.write_face(path, tbwf.default_spec(), Image.new("RGB", (454, 454)), font=font)
    return path


def test_check_passes_a_good_face(face, capsys):
    assert main(["check", str(face)]) == 0
    assert "OK" in capsys.readouterr().out


def test_check_fails_a_bad_face(tmp_path, capsys):
    bad = tmp_path / "bad.tbwf"
    bad.write_bytes(b"not a zip")
    assert main(["check", str(bad)]) == 1


def test_preview_writes_a_png(face, tmp_path):
    assert main(["preview", str(face), str(tmp_path / "p.png")]) == 0
    assert (tmp_path / "p.png").exists()


def test_font_score_lists_fonts(font, capsys):
    assert main(["font-score", str(font)]) == 0
    assert font.name in capsys.readouterr().out


def test_font_subset_writes_a_font(font, tmp_path):
    assert main(["font-subset", str(font), str(tmp_path / "o.ttf")]) == 0


def test_ble_commands_need_an_address():
    with pytest.raises(SystemExit):
        main(["query"])


def test_example_builds_a_valid_face(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", ["minimal_face.py", str(tmp_path / "e.tbwf")])
    runpy.run_path(str(ROOT / "examples" / "minimal_face.py"), run_name="__main__")
    assert tbwf.check_face(tmp_path / "e.tbwf") == []


def test_missing_face_is_a_message_not_a_traceback(tmp_path, capsys):
    assert main(["preview", str(tmp_path / "gone.tbwf"), str(tmp_path / "p.png")]) == 1
    assert "haylou: error" in capsys.readouterr().err


def test_preview_of_a_bad_file_is_a_message(tmp_path, capsys):
    bad = tmp_path / "bad.tbwf"
    bad.write_bytes(b"not a zip")
    assert main(["preview", str(bad), str(tmp_path / "p.png")]) == 1


def test_built_in_fonts_without_a_stand_in_is_a_message(tmp_path, capsys):
    path = tmp_path / "f.tbwf"
    tbwf.write_face(path, tbwf.default_spec(), Image.new("RGB", (454, 454)))
    assert main(["preview", str(path), str(tmp_path / "p.png")]) == 1
    assert "stand-in" in capsys.readouterr().err


def test_font_score_of_a_non_font_is_a_message(tmp_path, capsys):
    bad = tmp_path / "bad.ttf"
    bad.write_bytes(b"nope")
    assert main(["font-score", str(bad)]) == 1


def test_subset_refuses_to_overwrite_its_source(font, tmp_path):
    copy = tmp_path / "f.ttf"
    copy.write_bytes(font.read_bytes())
    assert main(["font-subset", str(copy), str(copy)]) == 1
    assert copy.read_bytes() == font.read_bytes()


def test_preview_names_what_it_did_not_draw(face, tmp_path, capsys):
    assert main(["preview", str(face), str(tmp_path / "p.png")]) == 0
    assert "stepResource" in capsys.readouterr().out
