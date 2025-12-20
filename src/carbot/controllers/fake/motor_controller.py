from carbot.contracts.motor_controller import MotorController


##Early Testing ok, TODO: record command plus call history instead!
class FakeMotorController(MotorController):
    def __init__(self) -> None:
        print("Initializing Fake Motor Controller")

    def close(self) -> None:
        print("Closing Fake Motor Controller")

    def set_wheels(self, fl: int, bl: int, fr: int, br: int) -> None:
        print(f"Setting Fake Motor to : {fl, bl, fr, br}")
