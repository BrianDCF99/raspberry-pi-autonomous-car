from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ._yaml import as_float, as_int, forbid_unknown_keys, require_key


@dataclass(frozen=True, slots=True)
class MotorConfig:
    max_power: int
    left_scale: float = 1.0
    right_scale: float = 1.0

    @staticmethod
    def from_mapping(data: Mapping[str, Any], *, path: Path) -> "MotorConfig":
        allowed = {"max_power", "left_scale", "right_scale"}
        forbid_unknown_keys(data, allowed, path=path)

        max_power = as_int(
            require_key(data, "max_power", path=path), key="max_power", path=path
        )
        left_scale = as_float(data.get("left_scale", 1.0), key="left_scale", path=path)
        right_scale = as_float(
            data.get("right_scale", 1.0), key="right_scale", path=path
        )

        return MotorConfig(
            max_power=max_power,
            left_scale=left_scale,
            right_scale=right_scale,
        )


@dataclass(frozen=True, slots=True)
class ServoConfig:
    pan_center: int
    tilt_center: int

    pan_min: int
    pan_max: int
    tilt_min: int
    tilt_max: int

    pan_offset: int = 0
    tilt_offset: int = 0

    @staticmethod
    def from_mapping(data: Mapping[str, Any], *, path: Path) -> "ServoConfig":
        allowed = {
            "pan_center",
            "tilt_center",
            "pan_min",
            "pan_max",
            "tilt_min",
            "tilt_max",
            "pan_offset",
            "tilt_offset",
        }
        forbid_unknown_keys(data, allowed, path=path)

        def req_int(k: str) -> int:
            return as_int(require_key(data, k, path=path), key=k, path=path)

        return ServoConfig(
            pan_center=req_int("pan_center"),
            tilt_center=req_int("tilt_center"),
            pan_min=req_int("pan_min"),
            pan_max=req_int("pan_max"),
            tilt_min=req_int("tilt_min"),
            tilt_max=req_int("tilt_max"),
            pan_offset=as_int(data.get("pan_offset", 0), key="pan_offset", path=path),
            tilt_offset=as_int(
                data.get("tilt_offset", 0), key="tilt_offset", path=path
            ),
        )


@dataclass(frozen=True, slots=True)
class InfraredConfig:
    hz: float = 2.0
    time_limit: float = 2.0

    @staticmethod
    def from_mapping(data: Mapping[str, Any], *, path: Path) -> "InfraredConfig":
        allowed = {"hz", "time_limit"}
        forbid_unknown_keys(data, allowed, path=path)

        def req_int(k: str) -> int:
            return as_int(require_key(data, k, path=path), key=k, path=path)

        return InfraredConfig(hz=req_int("hz"), time_limit=req_int("time_limit"))


@dataclass(frozen=True, slots=True)
class UltrasonicConfig:
    hz: float = 2.0
    time_limit: float = 2.0

    @staticmethod
    def from_mapping(data: Mapping[str, Any], *, path: Path) -> "UltrasonicConfig":
        allowed = {"hz", "time_limit"}
        forbid_unknown_keys(data, allowed, path=path)

        def req_int(k: str) -> int:
            return as_int(require_key(data, k, path=path), key=k, path=path)

        return UltrasonicConfig(hz=req_int("hz"), time_limit=req_int("time_limit"))


@dataclass(frozen=True, slots=True)
class CameraConfig:
    width: int = 640
    height: int = 480
    fps: int = 30
    device_idx: int = 0  # mainly for Mac/OpenCV

    @staticmethod
    def from_mapping(data: Mapping[str, Any], *, path: Path) -> "CameraConfig":
        allowed = {"width", "height", "fps", "device_idx"}
        forbid_unknown_keys(data, allowed, path=path)

        return CameraConfig(
            width=as_int(data.get("width", 640), key="width", path=path),
            height=as_int(data.get("height", 480), key="height", path=path),
            fps=as_int(data.get("fps", 30), key="fps", path=path),
            device_idx=as_int(data.get("device_idx", 0), key="device_idx", path=path),
        )


@dataclass(frozen=True, slots=True)
class CameraPolicy:
    time_limit: float
    retries: int
    idle_sleep: float

    @staticmethod
    def from_mapping(data: Mapping[str, Any], *, path: Path) -> "CameraPolicy":
        allowed = {"time_limit", "retries", "idle_sleep"}
        forbid_unknown_keys(data, allowed, path=path)

        time_limit = as_float(
            require_key(data, "time_limit", path=path), key="time_limit", path=path
        )
        if time_limit <= 0:
            raise ValueError(
                f"Key 'time_limit' in {path} must be > 0; got {time_limit}"
            )

        retries = as_int(
            require_key(data, "retries", path=path), key="retries", path=path
        )
        if retries < 0:
            raise ValueError(f"Key 'retries' in {path} must be >= 0; got {retries}")

        idle_sleep = as_float(
            require_key(data, "idle_sleep", path=path), key="idle_sleep", path=path
        )
        if idle_sleep < 0:
            raise ValueError(
                f"Key 'idle_sleep' in {path} must be >= 0; got {idle_sleep}"
            )

        return CameraPolicy(
            time_limit=time_limit, retries=retries, idle_sleep=idle_sleep
        )


@dataclass(frozen=True, slots=True)
class NetworkConfig:
    host: str = "0.0.0.0"
    port: int = 8080
    jpeg_quality: int = 75
    idle_sleep_s: float = 0.01

    @staticmethod
    def from_mapping(data: Mapping[str, Any], *, path: Path) -> "NetworkConfig":
        allowed = {"host", "port", "jpeg_quality", "idle_sleep_s"}
        forbid_unknown_keys(data, allowed, path=path)

        host_raw = data.get("host", "0.0.0.0")
        host = str(host_raw).strip()
        if not host:
            raise ValueError(f"Key 'host' in {path} must be a non-empty string")

        port = as_int(data.get("port", 8080), key="port", path=path)
        if not (1 <= port <= 65535):
            raise ValueError(f"Key 'port' in {path} must be in [1, 65535]; got {port}")

        jpeg_quality = as_int(
            data.get("jpeg_quality", 75), key="jpeg_quality", path=path
        )
        if not (10 <= jpeg_quality <= 95):
            raise ValueError(
                f"Key 'jpeg_quality' in {path} must be in [10, 95]; got {jpeg_quality}"
            )

        idle_sleep_s = as_float(
            data.get("idle_sleep_s", 0.01), key="idle_sleep_s", path=path
        )
        if idle_sleep_s < 0:
            raise ValueError(
                f"Key 'idle_sleep_s' in {path} must be >= 0; got {idle_sleep_s}"
            )

        return NetworkConfig(
            host=host,
            port=port,
            jpeg_quality=jpeg_quality,
            idle_sleep_s=idle_sleep_s,
        )


@dataclass(frozen=True, slots=True)
class RunConfig:
    # motors / servo / sensors (test | freenove)
    motor_controller: str | None = None
    motor_cfg: str | None = None

    servo_controller: str | None = None
    servo_cfg: str | None = None

    infrared_controller: str | None = None
    infrared_cfg: str | None = None

    ultrasonic_controller: str | None = None
    ultrasonic_cfg: str | None = None

    # camera (test | mac | pi)
    camera_controller: str | None = None
    camera_cfg: str | None = None
    camera_policy: str | None = None

    # networking / streaming
    networking: str | None = None

    @staticmethod
    def from_mapping(data: Mapping[str, Any], *, path: Path) -> "RunConfig":
        # allow your camera_test.yaml shorthand key: "controller"
        allowed = {
            "motor_controller",
            "motor_cfg",
            "servo_controller",
            "servo_cfg",
            "infrared_controller",
            "infrared_cfg",
            "ultrasonic_controller",
            "ultrasonic_cfg",
            "camera_controller",
            "camera_cfg",
            "camera_policy",
            "networking",
        }
        forbid_unknown_keys(data, allowed, path=path)

        def opt_nonempty_str(key: str) -> str | None:
            if key not in data or data[key] is None:
                return None
            s = str(data[key]).strip()
            if not s:
                raise ValueError(f"Key {key!r} in {path} must be a non-empty string")
            return s

        cfg = RunConfig(
            motor_controller=opt_nonempty_str("motor_controller"),
            motor_cfg=opt_nonempty_str("motor_cfg"),
            servo_controller=opt_nonempty_str("servo_controller"),
            servo_cfg=opt_nonempty_str("servo_cfg"),
            infrared_controller=opt_nonempty_str("infrared_controller"),
            infrared_cfg=opt_nonempty_str("infrared_cfg"),
            ultrasonic_controller=opt_nonempty_str("ultrasonic_controller"),
            ultrasonic_cfg=opt_nonempty_str("ultrasonic_cfg"),
            camera_controller=opt_nonempty_str("camera_controller"),
            camera_cfg=opt_nonempty_str("camera_cfg"),
            camera_policy=opt_nonempty_str("camera_policy"),
            networking=opt_nonempty_str("networking"),
        )

        # minimal cross-field validation (real dependencies only)
        if cfg.infrared_controller is not None and cfg.infrared_cfg is None:
            raise ValueError(
                f"If infrared controller is set in {path}, 'infrared_cfg' must also be set"
            )

        if cfg.camera_controller is not None:
            if cfg.camera_cfg is None:
                raise ValueError(
                    f"If camera controller is set in {path}, 'camera_cfg' must also be set"
                )
            if cfg.camera_policy is None:
                raise ValueError(
                    f"If camera controller is set in {path}, 'camera_policy' must also be set"
                )

        if cfg.networking is not None and cfg.camera_controller is None:
            raise ValueError(
                f"If 'networking' is set in {path}, a camera controller must also be set"
            )

        return cfg
