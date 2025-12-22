from carbot.contracts.ultrasonic_controller import UltrasonicController

class UltrasonicDriver:
    def __init__(self, controller: UltrasonicController) -> None:
        self._controller = controller
    
    def read(self) -> float | None:
        return self._controller.read_distance()
    
    def close(self) -> None:
        self._controller.close()