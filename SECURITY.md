# Safety and security

## Using it on a watch

This is an unofficial tool, used at your own risk, on watches you own. The MIT licence's "no warranty"
applies in full.

- **Unpairing deletes the data on the watch**, and this tool never does it for you.
- Pairing here can conflict with a pairing to the phone app.
- A `.tbwf` from someone else is a file you're choosing to trust. `haylou check` reads its structure,
  not its intent.

## The one rule

**Nothing here may write firmware or send face data to the watch directly.** A change that adds
firmware or upload commands, or uses the `d0ff` service, won't be merged, however useful it looks.
Faces go through the phone app. Tests pin the exact command list and keep `d0ff` out of the source.

## Privacy

Bluetooth addresses identify a device. Remove yours from anything you post, and from logs: `haylou`
prints frames, and they can contain your alert text.

## Reporting a problem

Open a private advisory under the repository's Security tab. For a safety problem that affects anyone
using the tool, please don't open a public issue first.

## Legal

This project is for interoperability with hardware you own. It includes no source, decompiled output
or assets from Hello Haylou. Its protocol knowledge did come from decompiling the app (see
[docs/reverse-engineering.md](docs/reverse-engineering.md)), so some details necessarily match it:
UUIDs, command ids, and file format names and values.

It doesn't bypass Hello Haylou's Premium mode, ads or any licence check, and changes that do won't
be merged.

Rules on reverse engineering vary by country, and you're responsible for following yours. If
you represent a rights holder and have a concern, please open an issue.
