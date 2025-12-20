from vendor.ultrasonic import Ultrasonic


class Ultrasonics:
    def __init__(self) -> None:
        self._ultrasonic = Ultrasonic()

    def close(self) -> None:
        self._ultrasonic.close()

    def get_distance(self) -> float | None:
        return self._ultrasonic.get_distance()
