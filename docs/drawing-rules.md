# How the app draws text

Faces look misaligned if you assume ordinary text layout. These rules come from reading Hello Haylou
3.7.19 and are what `haylou_tools.render` implements. They have **not** yet been measured against a
real screen, so please report differences.

- **Size:** pixels = screen width × `font.size`.
- **Measuring:** each element is measured on its own charset, not on what it's showing:

  | Element | Charset |
  |---|---|
  | Time and date numbers | `0123456789,-:/` |
  | Steps and heart rate | `0123456789,- ::/` |
  | Battery | the same plus a space |
  | Colon | `:` |

- **Vertical:** the top of the charset's tallest glyph sits at `y`. In many fonts `/` is taller than
  the digits, so digits land below `y`, while a lone colon starts exactly on it. To centre a colon on
  digits, give it a larger `y` (`haylou_tools.render.digit_centre` helps).
- **Horizontal:** numbers are drawn glyph by glyph in equal cells as wide as the charset's widest
  glyph, each glyph centred in its cell. Thin digits get gaps, so pick fonts with even digits.
- **Bounds:** all measurements are ink bounds, not advance widths.
- **Anchors:** left starts the string at `x`, centre shifts it by half its cell width, and right by
  all of it. A longer number grows away from the anchor.

## `dayOfWeek` is different

- It's drawn as a whole string, proportionally.
- Its box starts at `x` whatever the anchor. The anchor only moves the name inside a box as wide as
  the widest day name.
- Its top comes from the font's ascent, not its ink, so at the same `y` its baseline sits lower than
  a number's. Set `y` to match baselines.
- Names come from a locale, so they can be mixed case and accented (`Fri`, `sáb.`). A bundled font
  needs those glyphs.
