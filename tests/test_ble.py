import asyncio

import pytest

pytest.importorskip("bleak")

from haylou_tools import ble  # noqa: E402
from haylou_tools import protocol as p  # noqa: E402


def state_frame(state: int, challenge: int | None = None) -> bytes:
    body = b"\x58" + p.varint(state)
    if challenge:
        body += b"\x78" + p.varint(challenge)
    return p.frame(b"\x08\x01\x2a" + p.varint(len(body)) + body)


class FakeWatch:
    """Answers each pairing write with the next scripted reply."""

    def __init__(self, session, replies):
        self.session, self.replies, self.writes = session, list(replies), []

    async def write_gatt_char(self, uuid, data, response=False):
        self.writes.append((uuid, bytes(data)))
        if self.replies:
            # A real watch answers later, not in the middle of the write.
            reply = bytearray(self.replies.pop(0))
            asyncio.get_running_loop().call_soon(self.session._on_reply, None, reply)


def pair(replies):
    session = ble.Session("AA:BB:CC:DD:EE:FF")
    watch = FakeWatch(session, replies)
    asyncio.run(session.pair_with_code(watch, "1234"))
    return session, watch


@pytest.fixture(autouse=True)
def short_waits(monkeypatch):
    monkeypatch.setattr(ble, "FIRST_STATE_WAIT", 0.05)
    monkeypatch.setattr(ble, "NEXT_STATE_WAIT", 0.05)


def test_pairing_acks_each_state_until_paired():
    session, watch = pair([state_frame(5), state_frame(3), state_frame(1)])
    assert session.state == p.PairState.PAIRED
    assert sum(uuid == p.ACK_UUID for uuid, _ in watch.writes) == 3


def test_pairing_stops_on_failure():
    session, _ = pair([state_frame(2)])
    assert session.state == p.PairState.FAILED


def test_pairing_stops_when_the_watch_wants_a_key():
    session, watch = pair([state_frame(5, challenge=99)])
    assert session.key_requested
    assert sum(uuid == p.WRITE_UUID for uuid, _ in watch.writes) == 1


def test_a_silent_watch_times_out_without_an_error():
    assert pair([])[0].state is None


def test_a_malformed_pair_reply_is_ignored(capsys):
    session = ble.Session("AA:BB:CC:DD:EE:FF")
    session._on_reply(None, bytearray(p.frame(b"\x08\x01\x28\x01")))
    assert session.state is None


def test_acks_on_the_reply_channel_are_ignored():
    session = ble.Session("AA:BB:CC:DD:EE:FF")
    session._on_reply(None, bytearray(p.ACK))
    session._on_reply(None, bytearray(p.ACK))
    assert session.state is None


def test_a_bad_crc_doesnt_change_the_state():
    session = ble.Session("AA:BB:CC:DD:EE:FF")
    data = bytearray(state_frame(1))
    data[-1] ^= 0xFF
    session._on_reply(None, data)
    assert session.state is None


def test_a_truncated_status_is_ignored():
    session = ble.Session("AA:BB:CC:DD:EE:FF")
    session._on_reply(None, bytearray(p.frame(b"\x08\x01\x2a\x01\x58")))
    assert session.state is None


def test_a_challenge_in_any_state_stops_pairing():
    session, _ = pair([state_frame(3, challenge=99)])
    assert session.key_requested


class FakeClient(FakeWatch):
    """Stands in for BleakClient, replying to writes on the notify callback it was given."""

    def __init__(self, replies):
        self.replies, self.writes, self.on_reply = list(replies), [], None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def start_notify(self, _, callback):
        self.on_reply = callback

    async def write_gatt_char(self, uuid, data, response=False):
        self.writes.append((uuid, bytes(data)))
        if self.replies:
            reply = bytearray(self.replies.pop(0))
            asyncio.get_running_loop().call_soon(self.on_reply, None, reply)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(ble, "REPLY_WAIT", 0)

    def fake(replies):
        watch = FakeClient(replies)
        monkeypatch.setattr(ble, "BleakClient", lambda *_, **__: watch)
        return watch

    return fake


def test_query_asks_for_firmware_and_battery_and_reports_a_reply(client):
    watch = client([p.frame(b"\x08\x02\x10\x01")])
    assert asyncio.run(ble.query("AA:BB:CC:DD:EE:FF"))
    assert len(watch.writes) == 2


def test_query_reports_silence(client):
    client([])
    assert not asyncio.run(ble.query("AA:BB:CC:DD:EE:FF"))


def test_notify_sends_one_alert(client):
    watch = client([])
    asyncio.run(ble.notify("AA:BB:CC:DD:EE:FF", "Hi", "There"))
    assert len(watch.writes) == 1 and b"There" in watch.writes[0][1]


def test_pair_shows_an_alert_once_paired(client):
    watch = client([p.frame(b"\x08\x1f\x10\x01"), state_frame(5), state_frame(1)])
    assert asyncio.run(ble.pair("AA:BB:CC:DD:EE:FF", "1234", "Hi", "Paired"))
    assert b"Paired" in watch.writes[-1][1]


def test_pair_sends_no_alert_when_it_fails(client):
    watch = client([p.frame(b"\x08\x1f\x10\x01"), state_frame(2)])
    assert not asyncio.run(ble.pair("AA:BB:CC:DD:EE:FF", "1234", "Hi", "Paired"))
    assert not any(b"Paired" in data for _, data in watch.writes)
