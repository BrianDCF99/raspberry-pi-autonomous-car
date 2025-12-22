from carbot.contracts.ultrasonic_controller import UltrasonicController

class FakeUltrasonicController(UltrasonicController):
    def __init__(self) -> None:
        self._distance = 0.00
        print("Initializing Fake Ultrasonic Controller")
    
    def close(self) -> None:
        print("Closing Fake Ultrasonic Controller")

    def read_distance(self) -> float | None:
        return self._distance
    
    def set_distance(self, distance: float) -> None:
        self._distance = distance
