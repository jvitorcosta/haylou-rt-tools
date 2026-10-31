"""Prepare fonts for bundling in a face."""

from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

from .render import NUMBER, ink_box

# Latin-1 keeps accents, because day names come from the phone's locale (sáb.).
LATIN_1 = list(range(0x20, 0x7F)) + list(range(0xA0, 0x100))
MEASURE_SIZE = 200


def digit_spread(font_path: str | Path) -> float:
    """Narrowest digit ÷ widest. Digits go in equal cells, so a low score leaves holes around a 1."""
    boxes = [ink_box(str(font_path), MEASURE_SIZE, c) for c in NUMBER]
    widths = [box[2] - box[0] for box in boxes]
    if not max(widths):
        raise ValueError("%s has no digits" % font_path)
    return min(widths) / max(widths)


def subset_font(src: str | Path, out: str | Path, axes: dict[str, float] | None = None) -> None:
    """Save a Latin-1 copy of a font, pinning `axes` of a variable font (pin them all for a static one)."""
    if Path(out).exists() and Path(out).samefile(src):
        raise ValueError("refusing to overwrite the source font: %s" % src)
    font = TTFont(src)
    if axes:
        if "fvar" not in font:
            raise ValueError("%s is not a variable font" % src)
        font = instancer.instantiateVariableFont(font, axes)
    options = subset.Options()
    options.layout_features = []
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=LATIN_1)
    subsetter.subset(font)
    font.save(out)
