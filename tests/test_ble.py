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
