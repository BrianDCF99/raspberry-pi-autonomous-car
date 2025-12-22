from carbot.contracts.ultrasonic_controller import UltrasonicController
from .vendor.ultrasonic import Ultrasonic


class FreenoveUltrasonicController(UltrasonicController):
    def __init__(self) -> None:
        self._ultrasonic = Ultrasonic()

    def close(self) -> None:
        self._ultrasonic.close()

    def read_distance(self) -> float | None:
        return self._ultrasonic.get_distance()
