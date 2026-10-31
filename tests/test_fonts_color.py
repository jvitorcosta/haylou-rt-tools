import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from haylou_tools.color import contrast, to_argb, to_rgba
from haylou_tools.fonts import digit_spread, subset_font


def test_digit_spread_of_an_even_font(font):
    assert 0.7 <= digit_spread(font) <= 1


def test_subset_keeps_accents_and_drops_the_rest(font, tmp_path):
    out = tmp_path / "out.ttf"
    subset_font(font, out)
    codes = TTFont(out).getBestCmap()
    assert ord("á") in codes and max(codes) <= 0xFF


def test_subset_rejects_an_axis_on_a_static_font(font, tmp_path):
    with pytest.raises(ValueError, match="variable"):
        subset_font(font, tmp_path / "out.ttf", {"wght": 900})


def test_contrast_of_black_on_white_is_21():
    assert contrast("#000000", "#FFFFFF") == pytest.approx(21)


def test_contrast_ignores_order():
    assert contrast("#123456", "#FEDCBA") == contrast("#FEDCBA", "#123456")


def test_to_rgba():
    assert to_rgba("#102030") == (0x10, 0x20, 0x30, 255)


def test_to_argb_is_a_signed_android_colour():
    assert to_argb("#FFFFFF") == -1 and to_argb("#000000") == -16777216


@pytest.fixture
def variable_font(tmp_path):
    """A tiny font with weight and width axes."""
    pen = TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.lineTo((500, 0))
    pen.lineTo((500, 500))
    pen.closePath()
    glyph = pen.glyph()
    builder = FontBuilder(1000)
    builder.setupGlyphOrder([".notdef", "A"])
    builder.setupCharacterMap({0x41: "A"})
    builder.setupGlyf({".notdef": glyph, "A": glyph})
    builder.setupHorizontalMetrics({".notdef": (600, 0), "A": (600, 0)})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": "Tiny", "styleName": "Regular"})
    builder.setupOS2()
    builder.setupPost()
    builder.setupFvar([("wght", 100, 400, 900, "Weight"), ("wdth", 75, 100, 125, "Width")], [])
    path = tmp_path / "tiny.ttf"
    builder.save(path)
    return path


def test_pinning_every_axis_makes_a_static_font(variable_font, tmp_path):
    out = tmp_path / "out.ttf"
    assert subset_font(variable_font, out, {"wght": 900, "wdth": 100}) is False
    assert "fvar" not in TTFont(out)


def test_pinning_some_axes_says_the_font_is_still_variable(variable_font, tmp_path):
    assert subset_font(variable_font, tmp_path / "out.ttf", {"wght": 900}) is True


def test_an_unknown_axis_is_named(variable_font, tmp_path):
    with pytest.raises(ValueError, match="nope"):
        subset_font(variable_font, tmp_path / "out.ttf", {"nope": 1})
