import pytest
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
