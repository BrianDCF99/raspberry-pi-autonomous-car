from __future__ import annotations

from collections.abc import Callable

from carbot.config.models import CameraConfig
from carbot.contracts.camera_controller import CameraController
from carbot.contracts.infrared_controller import InfraredController
from carbot.contracts.motor_controller import MotorController
from carbot.contracts.servo_controller import ServoController
from carbot.contracts.ultrasonic_controller import UltrasonicController


# -----------------------------
# Motor
# -----------------------------
def _motor_test() -> MotorController:
    from carbot.controllers.fake.motor_controller import FakeMotorController

    return FakeMotorController()


def _motor_freenove() -> MotorController:
    # lazy import so Mac dev doesn't require smbus/etc
    from carbot.controllers.freenove.motor_controller import FreenoveMotorController

    return FreenoveMotorController()


MOTOR_CONTROLLERS: dict[str, Callable[[], MotorController]] = {
    "test": _motor_test,
    "freenove": _motor_freenove,
}


# -----------------------------
# Servo
# -----------------------------
def _servo_test() -> ServoController:
    from carbot.controllers.fake.servo_controller import FakeServoController

    return FakeServoController()


def _servo_freenove() -> ServoController:
    from carbot.controllers.freenove.servo_controller import FreenoveServoController

    return FreenoveServoController()


SERVO_CONTROLLERS: dict[str, Callable[[], ServoController]] = {
    "test": _servo_test,
    "freenove": _servo_freenove,
}


# -----------------------------
# Infrared
# -----------------------------
def _infrared_test() -> InfraredController:
    from carbot.controllers.fake.infrared_controller import FakeInfraredController

    return FakeInfraredController()


def _infrared_freenove() -> InfraredController:
    from carbot.controllers.freenove.infrared_controller import (
        FreenoveInfraredController,
    )

    return FreenoveInfraredController()


INFRARED_CONTROLLERS: dict[str, Callable[[], InfraredController]] = {
    "test": _infrared_test,
    "freenove": _infrared_freenove,
}


# -----------------------------
# Ultrasonic
# -----------------------------
def _ultrasonic_test() -> UltrasonicController:
    from carbot.controllers.fake.ultrasonic_controller import FakeUltrasonicController

    return FakeUltrasonicController()


def _ultrasonic_freenove() -> UltrasonicController:
    from carbot.controllers.freenove.ultrasonic_controller import (
        FreenoveUltrasonicController,
    )

    return FreenoveUltrasonicController()


ULTRASONIC_CONTROLLERS: dict[str, Callable[[], UltrasonicController]] = {
    "test": _ultrasonic_test,
    "freenove": _ultrasonic_freenove,
}


# -----------------------------
# Camera
# (camera controllers often need config)
# -----------------------------
def _camera_test(cfg: CameraConfig) -> CameraController:
    from carbot.controllers.fake.camera_controller import FakeCameraController

    return FakeCameraController()


def _camera_mac(cfg: CameraConfig) -> CameraController:
    from carbot.controllers.mac.camera_controller import MacCameraController

    return MacCameraController(cfg)


def _camera_pi(cfg: CameraConfig) -> CameraController:
    # lazy import so Mac dev doesn't require picamera2
    from carbot.controllers.pi.camera_controller import PiCameraController

    return PiCameraController(cfg)


CAMERA_CONTROLLERS: dict[str, Callable[[CameraConfig], CameraController]] = {
    "test": _camera_test,
    "mac": _camera_mac,
    "pi": _camera_pi,
}
