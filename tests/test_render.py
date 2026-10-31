from conftest import FONT as FONT_PATH
from PIL import Image, ImageFont

from haylou_tools import tbwf
from haylou_tools.render import (
    CHARSETS,
    DAYS_EN,
    digit_centre,
    draw_face,
    draw_value,
    glyph_cell,
    preview_face,
    size_px,
)

FONT = str(FONT_PATH)
DIGITS = CHARSETS["hour"]


def element(x=0.5, y=0.5, size=0.2, properties=16):
    return {
        "font": {"family": "x", "size": size},
        "color": {"colors": [-1]},
        "visible": True,
        "x": x,
        "y": y,
        "properties": properties,
    }


def ink(value, charset=DIGITS, whole=False, **kwargs):
    canvas = Image.new("RGB", (454, 454))
    draw_value(canvas, element(**kwargs), value, charset, FONT, whole)
    return canvas.getbbox()


def test_font_size_is_screen_width_times_size():
    assert size_px({"font": {"size": 0.2}}, 454) == 90


def test_lone_colon_top_sits_at_y():
    assert abs(ink(":", ":", y=100 / 454)[1] - 100) <= 1


def test_tallest_glyph_of_the_whole_set_sits_at_y():
    assert abs(ink("/", y=100 / 454)[1] - 100) <= 1
    assert ink("0", y=100 / 454)[1] >= ink("/", y=100 / 454)[1]


def test_charsets_include_the_separators():
    assert CHARSETS["hour"] == "0123456789,-:/"
    assert CHARSETS["step"] == CHARSETS["heartRate"] == "0123456789,- ::/"
    assert CHARSETS["battery"] == "0123456789,- ::/ "


def test_narrow_digit_is_centred_in_its_cell():
    cell = glyph_cell(FONT, 90, DIGITS)
    left, _, right, _ = ink("1", x=0.0)
    assert abs(left - (cell.width - right)) <= 1


def test_right_anchor_ends_at_x():
    assert 227 - 12 <= ink("10", x=0.5, properties=64)[2] <= 227


def test_centre_anchor_straddles_x():
    left, _, right, _ = ink("00", x=0.5, properties=32)
    assert abs((left + right) / 2 - 227) <= 2


def test_low_bits_do_not_change_the_anchor():
    assert ink("72", properties=20) == ink("72", properties=16)


def test_day_name_is_right_aligned_inside_a_box_starting_at_x():
    widest = glyph_cell(FONT, 90, DAYS_EN).width
    assert abs(ink("Fri", DAYS_EN, True, x=0.1, properties=65)[2] - (45 + widest)) <= 1


def test_day_name_baseline_comes_from_the_font_ascent():
    canvas = Image.new("RGB", (454, 454))
    draw_value(canvas, element(x=0.1, y=100 / 454, size=0.062), "Fri", DAYS_EN, FONT, True)
    ascent = ImageFont.truetype(FONT, 28).getmetrics()[0]
    assert abs(canvas.getbbox()[3] - (100 + ascent)) <= 1


def test_digit_centre_lands_on_the_digits():
    box = ink("0", y=100 / 454)
    assert abs((box[1] + box[3]) / 2 - (100 + digit_centre(FONT, 90, DIGITS))) <= 2


def test_draw_face_skips_hidden_elements_and_rounds_the_screen():
    hidden = element()
    hidden["visible"] = False
    out = draw_face(
        Image.new("RGB", (454, 454), "white"), {"elements": {"hour": hidden}}, {"hour": "10"}, FONT
    )
    assert out.getpixel((0, 0)) == (0, 0, 0) and out.getpixel((227, 227)) == (255, 255, 255)


def test_preview_uses_the_font_bundled_in_the_face(tmp_path):
    spec = tbwf.default_spec()
    tbwf.write_face(tmp_path / "f.tbwf", spec, Image.new("RGB", (454, 454)), font=FONT_PATH)
    out = tmp_path / "p.png"
    preview_face(tmp_path / "f.tbwf", out)
    assert Image.open(out).size == (240, 240) and Image.open(out).getbbox()


def test_preview_of_built_in_fonts_uses_the_stand_in(tmp_path):
    tbwf.write_face(tmp_path / "f.tbwf", tbwf.default_spec(), Image.new("RGB", (454, 454)))
    out = tmp_path / "p.png"
    preview_face(tmp_path / "f.tbwf", out, font=FONT)
    assert out.exists()
