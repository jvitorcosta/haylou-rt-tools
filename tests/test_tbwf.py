import json
import zipfile

import pytest
from PIL import Image

from haylou_tools import tbwf
from haylou_tools.color import to_argb

ELEMENTS = 30


def face(path, **kwargs):
    tbwf.write_face(path, tbwf.default_spec(), Image.new("RGB", (tbwf.DIAL_SIZE, tbwf.DIAL_SIZE)), **kwargs)
    return path


def test_default_spec_lists_every_element():
    assert len(tbwf.default_spec()["elements"]) == ELEMENTS


def test_written_face_passes_the_check(tmp_path):
    assert tbwf.check_face(face(tmp_path / "f.tbwf")) == []


def test_written_face_has_a_png_for_each_battery_level(tmp_path):
    names = zipfile.ZipFile(face(tmp_path / "f.tbwf")).namelist()
    assert sum("batteryResource/percent_" in n for n in names) == 11


def test_font_family_matches_its_zip_entry(tmp_path, font):
    path = face(tmp_path / "f.tbwf", font=font)
    assert "/font/" + font.name in zipfile.ZipFile(path).namelist()


def test_check_finds_a_missing_font(tmp_path):
    path = tmp_path / "f.tbwf"
    spec = tbwf.default_spec()
    spec["elements"]["hour"]["font"]["family"] = "/font/gone.ttf"
    tbwf.write_face(path, spec, Image.new("RGB", (454, 454)))
    assert any("gone.ttf" in problem for problem in tbwf.check_face(path))


def test_check_finds_a_missing_element(tmp_path):
    path = tmp_path / "f.tbwf"
    spec = tbwf.default_spec()
    del spec["elements"]["step"]
    tbwf.write_face(path, spec, Image.new("RGB", (454, 454)))
    assert any("step" in problem for problem in tbwf.check_face(path))


def test_check_rejects_a_file_that_is_not_a_zip(tmp_path):
    path = tmp_path / "f.tbwf"
    path.write_bytes(b"dial\xff\xff\xff\xff")
    assert tbwf.check_face(path)


def test_read_face_returns_spec_and_dial(tmp_path):
    loaded = tbwf.read_face(face(tmp_path / "f.tbwf"))
    assert loaded.dial.size == (454, 454) and loaded.spec["version"] == 1


def test_spec_is_written_as_json(tmp_path):
    z = zipfile.ZipFile(face(tmp_path / "f.tbwf"))
    assert json.loads(z.read("TiBoWaFe.json"))["caseShape"] == "round"


def test_default_gold_is_ffc24d():
    assert tbwf.GOLD == to_argb("#FFC24D")


@pytest.mark.parametrize(
    "spec",
    [[1], {"elements": [1]}, {"elements": {"hour": 1}}, {"elements": {"hour": {"font": {"family": None}}}}],
)
def test_check_reports_a_wrong_shape_instead_of_crashing(tmp_path, spec):
    path = tmp_path / "f.tbwf"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(tbwf.SPEC_NAME, json.dumps(spec))
    assert tbwf.check_face(path)


def test_check_reports_a_missing_file(tmp_path):
    assert tbwf.check_face(tmp_path / "gone.tbwf")


def test_check_finds_a_wrong_dial_size(tmp_path):
    path = tmp_path / "f.tbwf"
    tbwf.write_face(path, tbwf.default_spec(), Image.new("RGB", (100, 100)))
    assert any("454" in problem for problem in tbwf.check_face(path))


def test_write_face_leaves_the_callers_spec_alone(tmp_path, font):
    spec = tbwf.default_spec()
    tbwf.write_face(tmp_path / "f.tbwf", spec, Image.new("RGB", (454, 454)), font=font)
    assert spec == tbwf.default_spec()


def test_a_missing_font_leaves_no_partial_face(tmp_path):
    path = tmp_path / "f.tbwf"
    with pytest.raises(OSError):
        tbwf.write_face(path, tbwf.default_spec(), Image.new("RGB", (454, 454)), font=tmp_path / "gone.ttf")
    assert not path.exists()


def test_default_day_name_is_short():
    assert tbwf.default_spec()["elements"]["dayOfWeek"]["properties"] & 7 == 1


def test_default_battery_shows_one_percent_sign():
    assert not tbwf.default_spec()["elements"]["battery"]["properties"] & 4


def test_read_face_releases_the_file(tmp_path):
    path = face(tmp_path / "f.tbwf")
    tbwf.read_face(path)
    path.unlink()
