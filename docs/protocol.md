# BLE protocol

Tested on a Haylou RT with firmware `V21.01.004.2.1.1.3.51`. The watch advertises as `Haylou RT` with
service `fee7`, and connects without bonding.

## GATT

The UUIDs share the suffix `-3c17-d293-8e48-14fe2e4da212`.

| UUID | Properties | Role |
|---|---|---|
| `000001ff` | service | Main command service |
| `000002ff` | write without response | Commands |
| `000004ff` | write | Acknowledgements (`66 77 00 00 00 00 00`) |
| `000005ff` | notify | Replies |
| `000003ff` | indicate | Second reply channel |
| `0000d0ff` | service | Looks like firmware update. **Do not touch** |

Standard heart rate (`180d`/`2a37`) and Immediate Alert (`1802`/`2a06`) are also present.

## Frames

Every command and reply is a 9-byte header plus a protobuf payload:

```
7E 6D 03 | len (u16 LE) | crc16 (u16 LE) | sum (u16 LE) | payload
```

- `len` is the payload length.
- `crc16` covers the payload: polynomial `0x1021`, init `0`, MSB first, no reflection.
- `sum` is the byte sum of the 7 bytes before it.
- Replies use type 5, 6 or 7 instead of 3, and arrive in 20-byte notifications even though the MTU
  is 247, so join them using `len`.

In the payload, field 1 is the command, field 2 a sub-id, and field 3 the time.

Field 45 is the timezone: hundredths of an hour east of UTC, or whole hours as a 10-byte negative
varint west of it. The watch's time in replies looks like local time written as if it were UTC.

## Commands

| Command | Id |
|---|---|
| Pair (user info and key) | 1 |
| Query firmware | 2 |
| Text alert | 19 |
| Query battery | 21 |
| Auth send key (changes nothing, just a query) | 31 |

A query is `{1: id, 2: 0, 3: unix seconds}` plus the timezone. The watch answers with
`66 77 00 00 00 00 00` on `03ff`, then a frame on `05ff`. Firmware is in reply field 6, and battery in
field 25 as `{1: 0, 2: percent}`. Battery can take up to 12 s, and the standard `2a19` read returned 0.

## Text alerts

Command 19, with this message in field 23 (`BA 01 <len>`):

```
08 <app> 10 <title len> 18 <body len> 22 00 2A <title len> <title> 32 <body len> <body> 38 <time>
```

`<app>` is the alert type, `0E` for a generic message. The watch acknowledges every alert, but shows
it only when paired, so the reply proves nothing.

## Pairing

1. Send command 1 with user info (gender, age, height, weight, wrist) and twelve zero bytes as the key.
2. The reply's field 5 holds the state in sub-field 11, and a possible challenge in sub-field 15.
3. Ack each state change on `04ff`. **The watch doesn't advance without this.**
4. With no challenge, wait up to 6 s for the next state.

| State | Meaning |
|---|---|
| 1 | Paired |
| 2, 4 | Failed |
| 3, 5 | Waiting, or wants a key |

A watch that sends a challenge wants a key derived from a code. That has never been seen here, so
it isn't implemented.

The code is any 4 digits the user picks, not a Haylou secret; it sets one byte of the id. Keep the
screen on and the watch off the charger. Seen on the watch: states 5, 3, 1 about 4 to 5 s apart, using the zero key.

Still unknown: whether pairing lasts across connections, and whether Haylou Fun still connects
afterwards.
