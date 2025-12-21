from __future__ import annotations

from carbot.contracts.infrared_controller import Channel, InfraredController


class FakeInfraredController(InfraredController):
    _BIT_INDEX_MAP: dict[Channel, int] = {
        Channel.LEFT: 2,
        Channel.MIDDLE: 1,
        Channel.RIGHT: 0,
    }

    def __init__(self) -> None:
        self._bits: int = 0

    def close(self) -> None:
        print("Closing Fake Infrared Controller")

    def set_bits(self, left: int, middle: int, right: int) -> None:
        self._bits = ((left & 1) << 2) | ((middle & 1) << 1) | (right & 1)

    def read_channel(self, channel: Channel) -> int:
        return (self._bits >> self._BIT_INDEX_MAP[channel]) & 1
