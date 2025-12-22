from carbot.contracts.infrared_controller import Channel, InfraredController
from carbot.controllers.freenove.vendor.infrared import Infrared


class FreenoveInfraredController(InfraredController):
    _VENDOR_CH: dict[Channel, int] = {
        Channel.LEFT: 1,
        Channel.MIDDLE: 2,
        Channel.RIGHT: 3,
    }

    def __init__(self) -> None:
        self._infrared = Infrared()

    def close(self) -> None:
        self._infrared.close()

    def read_channel(self, channel: Channel) -> int:
        return self._infrared.read_one_infrared(self._VENDOR_CH[channel])
