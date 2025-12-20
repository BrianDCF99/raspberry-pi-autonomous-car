from carbot.contracts.servo_controller import ServoController


class FakeServoController(ServoController):
    def __init__(self) -> None:
        print("Initializing Fake Servo Controller")

    def set_angle(self, axis, angle) -> None:
        print(f"Angle: {axis.name} set to {angle} degrees")

    def close(self) -> None:
        print("Closing Fake Servo Controller")
