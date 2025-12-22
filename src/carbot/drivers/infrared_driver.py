from carbot.contracts.infrared_controller import Channel, InfraredController


class InfraredDriver:
    def __init__(self, controller: InfraredController) -> None:
        self._controller = controller

    def close(self) -> None:
        self._controller.close()

    def read_channel(self, channel: Channel) -> int:
        return self._controller.read_channel(channel)

    def read_tuple(self) -> tuple[int, int, int]:
        return (
            self.read_channel(Channel.RIGHT),
            self.read_channel(Channel.MIDDLE),
            self.read_channel(Channel.LEFT),
        )

    def read_bits(self) -> int:
        left, mid, right = self.read_tuple()
        return (left << 2) | (mid << 1) | right
