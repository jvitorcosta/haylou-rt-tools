from pathlib import Path

import pytest

from haylou_tools import protocol as p

NOW = 1_800_000_000


def test_crc16_matches_the_xmodem_check_value():
    assert p.crc16(b"123456789") == 0x31C3


def test_empty_frame_header():
    assert p.frame(b"") == bytes.fromhex("7e6d03 0000 0000 ee00")


@pytest.mark.parametrize("value, encoded", [(0, "00"), (127, "7f"), (128, "8001"), (300, "ac02")])
def test_varint(value, encoded):
    assert p.varint(value) == bytes.fromhex(encoded)


def test_timezone_east_of_utc_is_in_hundredths_of_an_hour():
    assert p.timezone_field(5400) == b"\xe8\x02" + p.varint(150)


def test_timezone_west_of_utc_rounds_towards_zero_like_the_app():
    assert p.timezone_field(-12600) == p.timezone_field(-3 * 3600)


def test_timezone_west_of_utc_is_whole_hours_as_a_ten_byte_varint():
    field = p.timezone_field(-3 * 3600)
    assert field[:2] == b"\xe8\x02" and len(field) == 12


def test_query_round_trips_through_the_parser():
    parsed = p.parse_frame(p.query(p.Command.QUERY_BATTERY, now=NOW, utc_offset=0))
    assert parsed.crc_ok and p.fields(parsed.payload)[1] == 21 and p.fields(parsed.payload)[3] == NOW


def test_parse_frame_flags_a_corrupt_payload():
    data = bytearray(p.query(p.Command.QUERY_FIRMWARE, now=NOW, utc_offset=0))
    data[-1] ^= 0xFF
    assert not p.parse_frame(bytes(data)).crc_ok


def test_parse_frame_rejects_foreign_bytes():
    with pytest.raises(ValueError):
        p.parse_frame(b"\x00" * 12)


def test_assembler_joins_split_notifications():
    data = p.query(p.Command.QUERY_FIRMWARE, now=NOW, utc_offset=0)
    assembler = p.FrameAssembler()
    assert assembler.feed(data[:5]) is None
    assert assembler.feed(data[5:]).crc_ok


def test_notification_keeps_long_utf8_text():
    body = "é" * 200
    parsed = p.parse_frame(p.notification("Olá", body, now=NOW, utc_offset=0))
    inner = p.fields(p.fields(parsed.payload)[23])
    assert inner[5].decode() == "Olá" and inner[6].decode() == body


def test_pairing_starts_with_a_zero_key():
    parsed = p.parse_frame(p.pairing("1234", now=NOW, utc_offset=0))
    assert p.fields(p.fields(parsed.payload)[4])[8] == bytes(12)


@pytest.mark.parametrize("code", ["123", "12345", "abcd", "\u0661\u0662\u0663\u0664"])
def test_pairing_rejects_a_bad_code(code):
    with pytest.raises(ValueError):
        p.pairing(code, now=NOW, utc_offset=0)


def test_describe_shows_nested_and_text_fields():
    lines = p.describe(b"\x08\x05\x12\x02hi")
    assert "field 1 = 5" in lines[0] and "'hi'" in lines[1]


def test_commands_are_exactly_the_safe_list():
    # The one rule of this project, see SECURITY.md: a new command must be added here on purpose.
    assert {command.value for command in p.Command} == {1, 2, 19, 21, 31}


def test_no_source_mentions_the_firmware_service():
    source = Path(p.__file__).parent
    assert not [f.name for f in source.glob("*.py") if "d0ff" in f.read_text(encoding="utf8").lower()]


def test_assembler_ignores_acks_between_frames():
    assembler = p.FrameAssembler()
    assert assembler.feed(p.ACK) is None and assembler.feed(p.ACK) is None


def test_assembler_ignores_an_ack_inside_a_split_frame():
    data = p.query(p.Command.QUERY_FIRMWARE, now=NOW, utc_offset=0)
    assembler = p.FrameAssembler()
    assembler.feed(data[:5])
    assembler.feed(p.ACK)
    assert assembler.feed(data[5:]).crc_ok


def test_assembler_drops_stray_bytes():
    assert p.FrameAssembler().feed(b"\x01\x02") is None


def test_varint_rejects_negative_numbers():
    with pytest.raises(ValueError):
        p.varint(-1)
