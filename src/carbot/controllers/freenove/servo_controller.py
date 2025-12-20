from __future__ import annotations

from carbot.contracts.servo_controller import Axis, ServoController

from .vendor.servo import Servo


class FreenoveServoController(ServoController):
    _CHANNEL_BY_AXIS: dict[Axis, str] = {Axis.PAN: "0", Axis.TILT: "1"}

    def __init__(self) -> None:
        self._servo = Servo()

    def set_angle(self, axis: Axis, angle: int) -> None:
        self._servo.set_servo_pwm(self._CHANNEL_BY_AXIS[axis], angle)

    def close(self) -> None:
        self._servo.close()
