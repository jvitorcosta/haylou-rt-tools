# haylou-rt-tools

Unofficial tools for the **Haylou RT (LS05S)** smartwatch: talk to it over Bluetooth, build custom
watch faces, and preview their main text on your PC using the text layout rules of the phone app.

**Status:** early

There's no official SDK for this watch. Everything here comes from observing the device and studying
how the Hello Haylou app works, for interoperability with a watch you own. Hello Haylou is an
independent app by a separate developer.

> [!WARNING]
> Unofficial, unaffiliated, and no warranty. It deliberately has **no firmware update or direct upload
> code**, so it can't flash your watch, but pairing can replace an existing pairing, and unpairing
> deletes the data on the watch. Read [SECURITY.md](SECURITY.md).

## Why I built it

The Haylou RT has no official SDK, so I worked out how the watch and its app talk and wrote these tools to build and preview my own watch faces.

## What works

| Feature | Status |
|---|---|
| Read firmware and battery | Tested on a real watch |
| Pair, and show a text alert in that connection | Tested on a real watch |
| Import a `.tbwf` through Hello Haylou | Tested with a community face |
| Generated faces on the watch | Not yet confirmed on a real screen |
| Preview of the main text elements | From reading the app; not yet measured against a real screen |

Firmware `V21.01.004.2.1.1.3.51`, Hello Haylou 3.7.19. Other versions and watches are untested.

## Install

Needs Python 3.10 or newer.

```bash
git clone https://github.com/jvitorcosta/haylou-rt-tools
cd haylou-rt-tools
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install ".[ble]"
```

## Make a face

Run these from the repository. The font is one this repository includes for its tests.

```bash
python examples/minimal_face.py my-face.tbwf
haylou check my-face.tbwf
haylou preview my-face.tbwf preview.png --font tests/data/nunito-black-latin1.ttf
```

Copy `my-face.tbwf` to your phone, open Hello Haylou (paired in Standalone mode), and import it from
the **Editor** tab. The Custom files tab only takes compiled `.bin` faces and rejects `.tbwf`.

The preview draws the time, date and stats in one font. Icons, hands and weather aren't drawn, and
the command lists anything it skipped.

To go further, copy [examples/minimal_face.py](examples/minimal_face.py) and change what it passes
to `write_face`: a background image, `font="my-font.ttf"` to bundle a font, or a changed spec.
[docs/tbwf-format.md](docs/tbwf-format.md) lists every element.

## Choose a font

Bundle only fonts whose licence allows it. The app puts digits in equal-width cells, so a font with a
thin `1` looks badly spaced. `font-score` measures that, and you should aim for 0.7 or more:

```bash
haylou font-score tests/data/nunito-black-latin1.ttf
```

`font-subset` cuts a font you've downloaded down to Latin-1 to keep the face small. With a variable
font, pin every axis:

```bash
haylou font-subset downloaded-font.ttf my-font.ttf --axis wght=900
```

## Talk to the watch

Turn off your phone's Bluetooth first: the watch stops advertising while it's connected.

```bash
haylou scan
haylou survey AA:BB:CC:DD:EE:FF
haylou query AA:BB:CC:DD:EE:FF
haylou pair AA:BB:CC:DD:EE:FF --code 1234
haylou notify AA:BB:CC:DD:EE:FF "Hello" "From my PC"
```

Pair with the watch off its charger and the screen on. `pair` shows an alert in the same connection,
which is the tested case. It isn't known yet whether `notify` works in a later connection, and the
watch acknowledges alerts even when it doesn't show them, so only trust what's on the screen.

A watch that asks for a pairing key isn't supported. Pairing sends a fixed profile (age 30, 170 cm,
70 kg), which the watch uses to estimate calories.

## Documentation

- [docs/protocol.md](docs/protocol.md): BLE services, frames, commands and pairing.
- [docs/tbwf-format.md](docs/tbwf-format.md): what's inside a `.tbwf`.
- [docs/drawing-rules.md](docs/drawing-rules.md): how the app positions text.
- [docs/reverse-engineering.md](docs/reverse-engineering.md): how all of this was worked out.

## Contributing

Reports from other watches and firmware versions are the most useful thing you can send. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

[MIT](LICENSE). Third-party parts are listed in [THIRD_PARTY.md](THIRD_PARTY.md). Haylou and Hello
Haylou belong to their respective owners.
