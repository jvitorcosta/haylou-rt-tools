"""Colours as a face needs them, from "#RRGGBB" strings."""


def to_rgba(color: str) -> tuple[int, int, int, int]:
    return tuple(int(color[i : i + 2], 16) for i in (1, 3, 5)) + (255,)


def to_argb(color: str) -> int:
    """Android's signed 32-bit colour, which TiBoWaFe.json stores."""
    return (0xFF << 24 | int(color[1:], 16)) - (1 << 32)


def _luminance(color: str) -> float:
    channels = [v / 255 for v in to_rgba(color)[:3]]
    r, g, b = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio, 1 to 21."""
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)
