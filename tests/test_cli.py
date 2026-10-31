import runpy
import zipfile
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


def test_a_timeout_says_so(monkeypatch, capsys):
    def time_out(*_):
        raise TimeoutError

    monkeypatch.setattr("haylou_tools.cli._run_ble", time_out)
    assert main(["query", "AA:BB:CC:DD:EE:FF"]) == 1
    assert "timed out" in capsys.readouterr().err


def test_preview_of_a_wrong_shape_is_a_message(tmp_path, capsys):
    path = tmp_path / "f.tbwf"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(tbwf.SPEC_NAME, "[1]")
        z.writestr(tbwf.DIAL_NAME, tbwf.png(Image.new("RGB", (454, 454))))
    assert main(["preview", str(path), str(tmp_path / "p.png")]) == 1
    assert "haylou: error" in capsys.readouterr().err


def test_preview_of_a_missing_key_is_a_message(tmp_path, font, capsys):
    spec = tbwf.default_spec()
    del spec["elements"]["hour"]["color"]
    path = tmp_path / "f.tbwf"
    tbwf.write_face(path, spec, Image.new("RGB", (454, 454)), font=font)
    assert main(["preview", str(path), str(tmp_path / "p.png")]) == 1
    assert "hour" in capsys.readouterr().err


def test_a_missing_font_is_named(tmp_path, capsys):
    assert main(["font-score", str(tmp_path / "gone.ttf")]) == 1
    assert "gone.ttf" in capsys.readouterr().err


def test_a_missing_stand_in_font_is_named(face, tmp_path, capsys):
    assert main(["preview", str(face), str(tmp_path / "p.png"), "--font", "gone.ttf"]) == 1
    assert "gone.ttf" in capsys.readouterr().err


def test_a_query_with_no_reply_fails(monkeypatch):
    async def silent(_):
        return False

    pytest.importorskip("bleak")
    monkeypatch.setattr("haylou_tools.ble.query", silent)
    assert main(["query", "AA:BB:CC:DD:EE:FF"]) == 1


def test_bluetooth_errors_are_messages(monkeypatch, capsys):
    ble = pytest.importorskip("haylou_tools.ble")

    async def fail(_):
        raise ble.BleakError("not found")

    monkeypatch.setattr(ble, "survey", fail)
    assert main(["survey", "AA:BB:CC:DD:EE:FF"]) == 1
    assert "not found" in capsys.readouterr().err


def test_a_partly_pinned_font_warns(monkeypatch, capsys, tmp_path, font):
    monkeypatch.setattr("haylou_tools.cli.subset_font", lambda *_: True)
    assert main(["font-subset", str(font), str(tmp_path / "o.ttf"), "--axis", "wght=700"]) == 0
    assert "pin every axis" in capsys.readouterr().out
