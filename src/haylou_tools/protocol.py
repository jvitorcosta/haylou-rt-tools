"""Build and read the watch's BLE frames. Pure code: no Bluetooth, clock or I/O unless asked.

Every command and reply is a 9-byte header plus a protobuf payload. See docs/protocol.md. There are
deliberately no firmware or upload commands here: see SECURITY.md.
"""

import struct
import time
from dataclasses import dataclass, field
from enum import IntEnum

_BASE = "-3c17-d293-8e48-14fe2e4da212"
WRITE_UUID = "000002ff" + _BASE
ACK_UUID = "000004ff" + _BASE
REPLY_UUIDS = ("000005ff" + _BASE, "000003ff" + _BASE)
ACK = bytes((0x66, 0x77, 0, 0, 0, 0, 0))

MAGIC = b"\x7e\x6d"
REQUEST_TYPE = 3
HEADER_SIZE = 9
ALERT_MESSAGE = 14
_ID_THIRD_BYTE = 176
# Tag and value: gender, age, height, weight, wrist, then a zero. The watch estimates calories from it.
_PROFILE = ((0x10, 1), (0x18, 30), (0x20, 170), (0x28, 70), (0x30, 0), (0x38, 0))


class Command(IntEnum):
    PAIR = 1
    QUERY_FIRMWARE = 2
    ALERT = 19
    QUERY_BATTERY = 21
    AUTH_SEND_KEY = 31


class PairState(IntEnum):
    PAIRED = 1
    FAILED = 2
    WANTS_KEY = 3
    FAILED_KEY = 4
    WAITING = 5


@dataclass(frozen=True)
class Frame:
    type: int
    payload: bytes
    crc_ok: bool


def varint(n: int) -> bytes:
    if n < 0:
        raise ValueError("varint of a negative number: mask it first")
    out = bytearray()
    while True:
        out.append((n & 0x7F) | (0x80 if n > 0x7F else 0))
        n >>= 7
        if not n:
            return bytes(out)


def read_varint(data: bytes, i: int) -> tuple[int, int]:
    n = shift = 0
    while True:
        b = data[i]
        i += 1
        n |= (b & 0x7F) << shift
        shift += 7
        if not b & 0x80:
            return n, i


def crc16(data: bytes) -> int:
    """CRC-16 with polynomial 0x1021, init 0, MSB first, no reflection."""
    crc = 0
    for byte in data:
        for i in range(8):
            bit = (byte >> (7 - i)) & 1
            top = (crc >> 15) & 1
            crc = (crc << 1) & 0xFFFF
            if bit ^ top:
                crc ^= 0x1021
    return crc


def frame(payload: bytes) -> bytes:
    head = MAGIC + bytes((REQUEST_TYPE,)) + struct.pack("<HH", len(payload), crc16(payload))
    return head + struct.pack("<H", sum(head) & 0xFFFF) + payload


def parse_frame(data: bytes) -> Frame:
    if data[:2] != MAGIC or len(data) < HEADER_SIZE:
        raise ValueError("not a frame: %s" % data[:HEADER_SIZE].hex(" "))
    size = struct.unpack_from("<H", data, 3)[0]
    payload = data[HEADER_SIZE : HEADER_SIZE + size]
    return Frame(data[2], payload, crc16(payload) == struct.unpack_from("<H", data, 5)[0])


@dataclass
class FrameAssembler:
    """Replies arrive split into 20-byte notifications; this joins them back into frames."""

    _pending: bytearray = field(default_factory=bytearray)

    def feed(self, data: bytes) -> Frame | None:
        if data == ACK:  # Acks share a channel with frames and can land between chunks.
            return None
        if data[:2] == MAGIC:
            self._pending = bytearray(data)
        elif self._pending:
            self._pending += data
        else:
            return None
        if len(self._pending) < HEADER_SIZE:
            return None
        if len(self._pending) < HEADER_SIZE + struct.unpack_from("<H", self._pending, 3)[0]:
            return None
        done = parse_frame(bytes(self._pending))
        self._pending = bytearray()
        return done


def _clock(now: int | None, utc_offset: int | None) -> tuple[int, int]:
    return (
        int(time.time()) if now is None else now,
        time.localtime().tm_gmtoff if utc_offset is None else utc_offset,
    )


def timezone_field(utc_offset: int) -> bytes:
    """Field 45: hundredths of an hour east of UTC, whole hours (a negative varint) west of it."""
    if utc_offset < 0:
        return b"\xe8\x02" + varint(int(utc_offset / 3600) & 0xFFFFFFFFFFFFFFFF)
    return b"\xe8\x02" + varint(utc_offset // 36)


def query(command: int, now: int | None = None, utc_offset: int | None = None) -> bytes:
    now, utc_offset = _clock(now, utc_offset)
    return frame(b"\x08" + varint(command) + b"\x10\x00\x18" + varint(now) + timezone_field(utc_offset))


def notification(title: str, body: str, now: int | None = None, utc_offset: int | None = None) -> bytes:
    """A text alert. It only shows on a paired watch, though an unpaired one still acknowledges it."""
    now, utc_offset = _clock(now, utc_offset)
    head, text, stamp = title.encode(), body.encode(), varint(now)
    inner = (
        b"\x08"
        + varint(ALERT_MESSAGE)
        + b"\x10"
        + varint(len(head))
        + b"\x18"
        + varint(len(text))
        + b"\x22\x00"
        + b"\x2a"
        + varint(len(head))
        + head
        + b"\x32"
        + varint(len(text))
        + text
        + b"\x38"
        + stamp
    )
    alert = b"\x08" + varint(Command.ALERT) + b"\x10\x00\x18" + stamp
    return frame(alert + b"\xba\x01" + varint(len(inner)) + inner + timezone_field(utc_offset))


def pairing(code: str, now: int | None = None, utc_offset: int | None = None) -> bytes:
    """Command 1 with a fixed profile and a zero key, which is all a watch has needed so far.

    A watch can answer with a challenge, which needs a key this project doesn't implement.
    """
    if len(code) != 4 or not (code.isascii() and code.isdigit()):
        raise ValueError("the pairing code must be 4 digits")
    now, utc_offset = _clock(now, utc_offset)
    code_hash = 0
    for c in code:
        code_hash = code_hash * 31 + ord(c)
    # The id's third byte follows from the code; the other bytes are what the app sends.
    identity = b"\x08\xba\xc2" + bytes((_ID_THIRD_BYTE + code_hash % 10,)) + b"\x05"
    body = identity + b"".join(bytes((tag,)) + varint(value) for tag, value in _PROFILE)
    body += b"\x42\x0c" + bytes(12)
    head = b"\x08" + varint(Command.PAIR) + b"\x10\x00\x18" + varint(now)
    return frame(head + b"\x22" + varint(len(body)) + body + timezone_field(utc_offset))


def fields(data: bytes) -> dict[int, int | bytes]:
    """Top-level varint and length-delimited fields of a protobuf message."""
    out: dict[int, int | bytes] = {}
    i = 0
    while i < len(data):
        tag, i = read_varint(data, i)
        if tag & 7 == 0:
            out[tag >> 3], i = read_varint(data, i)
        elif tag & 7 == 2:
            size, i = read_varint(data, i)
            out[tag >> 3] = data[i : i + size]
            i += size
        else:
            break
    return out


def describe(data: bytes, indent: str = "    ") -> list[str]:
    """Readable lines for a protobuf message with no schema. Binary fields are tried as messages."""
    lines = []
    i = 0
    while i < len(data):
        tag, i = read_varint(data, i)
        number, wire = tag >> 3, tag & 7
        if wire == 0:
            value, i = read_varint(data, i)
            lines.append("%sfield %d = %d" % (indent, number, value))
        elif wire == 2:
            size, i = read_varint(data, i)
            value = data[i : i + size]
            i += size
            text = value.decode("utf-8", errors="replace")
            lines.append("%sfield %d (%d bytes) = %s  %r" % (indent, number, size, value.hex(" "), text))
            if value and not text.isprintable():
                try:
                    lines += describe(value, indent + "    ")
                except IndexError:
                    pass
        elif wire in (1, 5):
            width = 8 if wire == 1 else 4
            lines.append("%sfield %d = %s" % (indent, number, data[i : i + width].hex(" ")))
            i += width
        else:
            lines.append("%sfield %d: wire type %d, stopping" % (indent, number, wire))
            break
    return lines
