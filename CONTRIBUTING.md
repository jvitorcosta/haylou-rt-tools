# Contributing

Thanks for helping. The most useful contributions need no code:

- **Watch reports.** Open an issue with your watch, firmware and app version, and what worked, even
  when the answer is "it doesn't work". Remove your Bluetooth address first.
- **Screen comparisons.** A photo of a face beside its `haylou preview`, because the drawing rules
  haven't been measured on a real screen yet.

## The rules

- Nothing here may write firmware or upload to the watch directly: see [SECURITY.md](SECURITY.md).
- Decompiled code doesn't go in this repository, in commits, issues or pull requests. Describe
  behaviour in your own words.
- Bundled fonts and art must have a licence that allows it, listed in [THIRD_PARTY.md](THIRD_PARTY.md).

## Working on it

```bash
pip install -e ".[ble,dev]"
ruff check .
ruff format --check .
python -m pytest
```

- Keep Bluetooth out of `protocol.py`, so it can be tested without a watch.
- New behaviour comes with a test that fails without it.
- Commits use [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): subject`.
- Say in your pull request what you tested on a real watch, if anything. Don't mark something
  "Tested" in the README unless it ran on one.
