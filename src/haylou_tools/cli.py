"""The `haylou` command."""

import argparse
import asyncio
import sys
import zipfile

from PIL import UnidentifiedImageError

from . import __version__
from .fonts import digit_spread, subset_font
from .render import preview_face
from .tbwf import check_face

EXPECTED_ERRORS = (
    OSError,
    ValueError,
    KeyError,
    zipfile.BadZipFile,
    UnidentifiedImageError,
    asyncio.TimeoutError,
)


def _ble():
    try:
        from . import ble
    except ImportError:
        sys.exit("Bluetooth commands need bleak: pip install bleak")
    return ble


def _run_ble(name: str, *args):
    ble = _ble()
    try:
        return asyncio.run(getattr(ble, name)(*args))
    except ble.BleakError as error:
        raise OSError(str(error)) from error


def _scan(args) -> int:
    _run_ble("scan", args.seconds)
    return 0


def _survey(args) -> int:
    _run_ble("survey", args.address)
    return 0


def _query(args) -> int:
    _run_ble("query", args.address)
    return 0


def _notify(args) -> int:
    _run_ble("notify", args.address, args.title, args.body)
    return 0


def _pair(args) -> int:
    if len(args.code) != 4 or not (args.code.isascii() and args.code.isdigit()):
        raise ValueError("the pairing code must be 4 digits")
    paired = _run_ble("pair", args.address, args.code, args.title, args.body)
    return 0 if paired else 1


def _check(args) -> int:
    problems = check_face(args.face)
    for problem in problems:
        print(problem)
    if not problems:
        print("OK")
    return 1 if problems else 0


def _preview(args) -> int:
    undrawn = preview_face(args.face, args.out, args.font)
    if undrawn:
        print("Visible but not previewed: %s" % ", ".join(undrawn))
    return 0


def _font_score(args) -> int:
    for path in sorted(args.fonts, key=digit_spread, reverse=True):
        print("%.2f  %s" % (digit_spread(path), path))
    return 0


def _axis(value: str) -> tuple[str, float]:
    name, _, number = value.partition("=")
    return name, float(number)


def _font_subset(args) -> int:
    subset_font(args.src, args.out, dict(args.axis))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="haylou", description=__doc__)
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)

    def add(name, run, help_text):
        command = commands.add_parser(name, help=help_text)
        command.set_defaults(run=run)
        return command

    add("scan", _scan, "list nearby Bluetooth devices").add_argument("--seconds", type=float, default=10)
    add("survey", _survey, "list a device's services, read-only").add_argument("address")
    add("query", _query, "ask for firmware and battery").add_argument("address")
    notify = add("notify", _notify, "show a text alert on a paired watch")
    notify.add_argument("address")
    notify.add_argument("title")
    notify.add_argument("body")
    pair = add("pair", _pair, "pair, then show an alert to prove it worked")
    pair.add_argument("address")
    pair.add_argument("--code", default="1234", help="4-digit pairing code")
    pair.add_argument("--title", default="Haylou tools")
    pair.add_argument("--body", default="Paired")
    add("check", _check, "check a .tbwf for problems").add_argument("face")
    preview = add("preview", _preview, "preview a .tbwf's main text elements")
    preview.add_argument("face")
    preview.add_argument("out")
    preview.add_argument("--font", help="stand-in for a face that uses built-in fonts")
    add("font-score", _font_score, "rank fonts by digit evenness").add_argument("fonts", nargs="+")
    subset = add("font-subset", _font_subset, "make a static Latin-1 font for bundling")
    subset.add_argument("src")
    subset.add_argument("out")
    subset.add_argument("--axis", type=_axis, action="append", default=[], help="pin an axis, as wght=900")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.run(args)
    except KeyboardInterrupt:
        return 130
    except EXPECTED_ERRORS as error:
        print("haylou: error: %s" % error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
