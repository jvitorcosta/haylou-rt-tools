# The `.tbwf` format

A `.tbwf` is the editable face project Hello Haylou imports. Community faces use it too, for example
on [amazfitwatchfaces.com](https://amazfitwatchfaces.com/haylou/fresh?compatible=RT_LS05S). The app
compiles it into the binary face the watch runs.

## Which tab

Each tab takes one kind of file, and shows "Invalid watch face file" for any other, going by the
extension alone:

| Tab or action | Takes |
|---|---|
| Editor | `.tbwf` |
| Custom files | compiled `.bin` |
| Restore | backup `.zip` |

Pair the app in Standalone mode. Haylou Fun can block uploads.

## Contents

A ZIP with:

- `TiBoWaFe.json`: `aspectRatio`, `caseShape`, `version` and `elements`.
- `/resourceImage/dial.png`: the 454 × 454 background.
- `/resourceImage/...`: hands, connection icons, and `batteryResource/percent_0.png` to `percent_100.png`
  in steps of 10.
- `/font/*.ttf`: optional bundled fonts.

Yes, the entry names start with a slash.

## Elements

Keep all 30 and use `visible: false` to hide one. Each has `visible` and usually `x`, `y` (fractions
of the screen, top-left for images) and `color`.

- **Time:** `hour`, `timeSeparator`, `minute`, `second`, plus `hourHand`, `minuteHand`, `secondHand`.
- **Date:** `year`, `yearSeparator`, `month`, `dateSeparator`, `day`, `dayOfWeek`.
- **Stats:** `step`, `stepResource`, `stepGoalProgressResource`, `calorie`, `calorieResource`,
  `distance`, `distanceResource`, `heartRate`, `heartRateResource`.
- **Status:** `battery`, `batteryPercentSign`, `batteryResource`, `connectionResource`.
- **Weather:** `weatherTemperature`, `weatherTemperatureUnitSign`, `weatherResource`.
- **Images:** `dial`, plus `preview` in the app's own files.

## Fonts

`font.size` is a fraction of the screen width. `font.family` is either a file, as `/font/Name.ttf`
with a matching ZIP entry, or a built-in name:

- `sans-serif` with `-thin`, `-light`, `-medium` or `-black`
- `monospace`, `casual`
- Fira Sans Condensed, Rubik, Oswald and Big Shoulders Text weights

An unknown family without its file falls back to sans-serif.

## `properties`

| Bits | Element | Meaning |
|---|---|---|
| 16, 32, 64 | Text | Left, centre, right anchor |
| 1, 2, 4 | `dayOfWeek` | Short (`Fri`), full (`Friday`), narrow (`F`) |
| 4 | `battery` | Adds a shrunk `%` |
| 16, 32, 64 | Images | Fit, crop, stretch |

## Compiled faces

Compiled faces start with `dial FF FF FF FF`, then `TiBoWf10`, sizes, a table of elements and the
images. This project doesn't write them: the app does that safely.
