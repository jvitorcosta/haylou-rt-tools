# haylou-rt-tools

Unofficial tools for the **Haylou RT (LS05S)** smartwatch: talk to it over Bluetooth, build custom
watch faces, and preview their main text on your PC using the text layout rules of the phone app.

There's no official SDK for this watch. Everything here comes from observing the device and studying
how the Hello Haylou app works, for interoperability with a watch you own.

> [!WARNING]
> Unofficial, unaffiliated, and no warranty. It deliberately has **no firmware update or direct upload
> code**, so it can't flash your watch, but pairing can replace an existing pairing, and unpairing
> deletes the data on the watch. Read [SECURITY.md](SECURITY.md).

## What works

| Feature | Status |
|---|---|
| Read firmware and battery | Tested on a real watch |
| Pair, and show a text alert in that connection | Tested on a real watch |
| Import a `.tbwf` through Hello Haylou | Tested with a community face |
| `scripts/copy_to_phone.ps1` | Run on a real phone (see the changelog) |
| Generated faces on the watch | Not yet confirmed on a real screen |
| Preview of the main text elements | From reading the app; not yet measured against a real screen |

Firmware `V21.01.004.2.1.1.3.51`, Hello Haylou 3.7.19. Other versions and watches are untested.

## Install

Needs Python 3.10 or newer.

```bash
git clone https://github.com/jvitorcosta/haylou-rt-tools
```

```bash
cd haylou-rt-tools
```

```bash
pip install ".[ble]"
```

The API may change before 1.0.

## Make a face

```bash
python examples/minimal_face.py my-face.tbwf
haylou check my-face.tbwf
haylou preview my-face.tbwf preview.png --font some-font.ttf
```

Copy the file to your phone, open Hello Haylou (paired in Standalone mode), and import it from the
**Editor** tab. The Custom files tab only takes compiled `.bin` faces and rejects `.tbwf`.

On Windows, [scripts/copy_to_phone.ps1](scripts/copy_to_phone.ps1) copies over USB and verifies the
result.

The preview draws the time, date and stats. Icons, hands and weather aren't drawn, and the command
lists anything it skipped.

For anything beyond a background, change the spec:

```python
from PIL import Image
from haylou_tools.render import CENTRE
from haylou_tools.tbwf import DIAL_SIZE, default_spec, write_face

spec = default_spec()
spec["elements"]["hour"].update(x=0.45, y=0.3, properties=CENTRE)
write_face("face.tbwf", spec, Image.open("background.png").resize((DIAL_SIZE, DIAL_SIZE)), font="my-font.ttf")
```

Bundle only fonts whose licence allows it, and subset them first:

```bash
haylou font-score a.ttf b.ttf
haylou font-subset Nunito-Variable.ttf my-font.ttf --axis wght=900
```

`font-score` matters more than it sounds: the app puts digits in equal-width cells, so a font with a
thin `1` looks badly spaced. Aim for 0.7 or more.

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

A watch that asks for a pairing key isn't supported.

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
Haylou are trademarks or names of their respective owners, and this project isn't connected to them.
