from enum import Enum, auto
from typing import Protocol


class Channel(Enum):
    LEFT = auto()
    MIDDLE = auto()
    RIGHT = auto()


class InfraredController(Protocol):
    def read_channel(self, channel: Channel) -> int: ...
    def close(self) -> None: ...
