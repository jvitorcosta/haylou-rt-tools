"""Talk to a real watch over BLE. Needs the `ble` extra (bleak).

The phone must not be holding the watch, so turn off its Bluetooth first.
"""

import asyncio
from collections.abc import Callable

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError  # noqa: F401

from . import protocol as p

NAME_HINTS = ("haylou", "ls05")
CONNECT_TIMEOUT = 20
REPLY_WAIT = 12
FIRST_STATE_WAIT = 20
NEXT_STATE_WAIT = 6
DONE_STATES = (p.PairState.PAIRED, p.PairState.FAILED, p.PairState.FAILED_KEY)


def _show(value: bytes) -> str:
    text = value.decode("utf-8", errors="replace")
    printable = all(c.isprintable() for c in text) and text.strip()
    return "%s  %r" % (value.hex(" "), text) if printable else value.hex(" ")


async def scan(seconds: float = 10) -> None:
    """List what's advertising, strongest first, with a star on what looks like a Haylou."""
    found = await BleakScanner.discover(timeout=seconds, return_adv=True)
    for device, advert in sorted(found.values(), key=lambda row: -row[1].rssi):
        name = advert.local_name or device.name or "?"
        looks_right = any(hint in name.lower() for hint in NAME_HINTS)
        print("%s %s  %4d dBm  %s" % ("*" if looks_right else " ", device.address, advert.rssi, name))


async def survey(address: str) -> None:
    """Read-only: list services and characteristics, and read the ones marked readable."""
    async with BleakClient(address, timeout=CONNECT_TIMEOUT) as client:
        for service in client.services:
            print("\n[service] %s  %s" % (service.uuid, service.description))
            for char in service.characteristics:
                print("  [char] %s  (%s)  %s" % (char.uuid, ",".join(char.properties), char.description))
                if "read" in char.properties:
                    try:
                        print("         value: %s" % _show(await client.read_gatt_char(char)))
                    except Exception as error:  # A refused read is a finding, not a failure.
                        print("         read failed: %s" % error)


class Session:
    """A connection that prints every frame it gets and tracks the pairing state."""

    def __init__(self, address: str):
        self.address = address
        self.state: int | None = None
        self.challenge: int | None = None
        self.key_requested = False
        self.replied = False
        self._changed = asyncio.Event()
        self._assembler = p.FrameAssembler()

    def _on_reply(self, sender, data: bytearray) -> None:
        done = self._assembler.feed(bytes(data))
        if done is None:
            return
        self.replied = True
        print("<- type %d, %d bytes, crc %s" % (done.type, len(done.payload), "ok" if done.crc_ok else "BAD"))
        if not done.crc_ok:
            return
        try:
            print("\n".join(p.describe(done.payload)))
            reply = p.fields(done.payload)
            status = reply.get(5)
            info = p.fields(status) if reply.get(1) == p.Command.PAIR and isinstance(status, bytes) else None
        except (IndexError, ValueError):
            print("    (payload isn't plain protobuf)")
            return
        if info is not None and (info.get(11), info.get(15)) != (self.state, self.challenge):
            self.state, self.challenge = info.get(11), info.get(15)
            self._changed.set()

    async def send(self, client: BleakClient, name: str, data: bytes) -> None:
        print("\n-> %s: %s" % (name, data.hex(" ")))
        await client.write_gatt_char(p.WRITE_UUID, data, response=False)

    async def pair_with_code(self, client: BleakClient, code: str) -> None:
        # Ack every state change and give the watch time between states.
        await self.send(client, "PAIR", p.pairing(code))
        wait = FIRST_STATE_WAIT
        while True:
            try:
                await asyncio.wait_for(self._changed.wait(), wait)
            except asyncio.TimeoutError:
                return
            self._changed.clear()
            wait = NEXT_STATE_WAIT
            await client.write_gatt_char(p.ACK_UUID, p.ACK, response=True)
            if self.state in DONE_STATES:
                return
            if self.challenge:
                self.key_requested = True
                print("This watch asked for a pairing key, which isn't supported.")
                return

    async def run(self, step: Callable) -> None:
        async with BleakClient(self.address, timeout=CONNECT_TIMEOUT) as client:
            for uuid in p.REPLY_UUIDS:
                await client.start_notify(uuid, self._on_reply)
            await step(client)


async def query(address: str) -> bool:
    """Ask for firmware and battery, and say whether the watch answered."""
    session = Session(address)

    async def step(client: BleakClient) -> None:
        for command in (p.Command.QUERY_FIRMWARE, p.Command.QUERY_BATTERY):
            await session.send(client, command.name, p.query(command))
            await asyncio.sleep(REPLY_WAIT)

    await session.run(step)
    return session.replied


async def notify(address: str, title: str, body: str) -> None:
    session = Session(address)

    async def step(client: BleakClient) -> None:
        await session.send(client, "ALERT", p.notification(title, body))
        await asyncio.sleep(REPLY_WAIT)
        print("Sent. The watch acknowledges alerts even when it doesn't show them.")

    await session.run(step)


async def pair(address: str, code: str, title: str, body: str) -> bool:
    """Pair with the watch's screen on, off the charger, and show an alert to prove it worked."""
    session = Session(address)

    async def step(client: BleakClient) -> None:
        await session.send(client, "AUTH_SEND_KEY", p.query(p.Command.AUTH_SEND_KEY))
        await asyncio.sleep(REPLY_WAIT)
        await session.pair_with_code(client, code)
        print("\nPairing state: %s" % session.state)
        if session.state == p.PairState.PAIRED:
            await session.send(client, "ALERT", p.notification(title, body))
            await asyncio.sleep(REPLY_WAIT)

    await session.run(step)
    return session.state == p.PairState.PAIRED
