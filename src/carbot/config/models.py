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

        hz = as_float(require_key(data, "hz", path=path), key="hz", path=path)
        time_limit = as_float(
            require_key(data, "time_limit", path=path), key="time_limit", path=path
        )

        if hz <= 0:
            raise ValueError(f"Key 'hz' in {path} must be > 0; got {hz}")
        if time_limit <= 0:
            raise ValueError(f"Key 'time_limit' in {path} must be > 0; got {time_limit}")

        return InfraredConfig(hz=hz, time_limit=time_limit)


@dataclass(frozen=True, slots=True)
class UltrasonicConfig:
    hz: float = 2.0
    time_limit: float = 2.0

    @staticmethod
    def from_mapping(data: Mapping[str, Any], *, path: Path) -> "UltrasonicConfig":
        allowed = {"hz", "time_limit"}
        forbid_unknown_keys(data, allowed, path=path)

        hz = as_float(require_key(data, "hz", path=path), key="hz", path=path)
        time_limit = as_float(
            require_key(data, "time_limit", path=path), key="time_limit", path=path
        )

        if hz <= 0:
            raise ValueError(f"Key 'hz' in {path} must be > 0; got {hz}")
        if time_limit <= 0:
            raise ValueError(f"Key 'time_limit' in {path} must be > 0; got {time_limit}")

        return UltrasonicConfig(hz=hz, time_limit=time_limit)


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



_KEY_ALIASES: dict[str, str] = {
    "UP": "\x1b[A",
    "DOWN": "\x1b[B",
    "RIGHT": "\x1b[C",
    "LEFT": "\x1b[D",
    "SPACE": " ",
    "ENTER": "\r",
    "TAB": "\t",
    "ESC": "\x1b",
    "CTRL_C": "\x03",
}


def _parse_key_token(tok: str, *, key: str, path: Path) -> str:
    s = tok.strip()
    if not s:
        raise ValueError(f"Key {key!r} in {path} contains an empty key token")

    # Named aliases
    alias = s.upper()
    if alias in _KEY_ALIASES:
        return _KEY_ALIASES[alias]

    # Hex escape like \x03 (single char only)
    if s.startswith("\\x"):
        try:
            decoded = bytes(s, "utf-8").decode("unicode_escape")
        except Exception as e:
            raise ValueError(
                f"Key {key!r} in {path} has invalid escape token {s!r}"
            ) from e
        if len(decoded) != 1:
            raise ValueError(
                f"Key {key!r} in {path} escape token must decode to 1 char: {s!r}"
            )
        return decoded

    # Single character
    if len(s) == 1:
        return s.lower()

    raise ValueError(
        f"Key {key!r} in {path} has invalid token {s!r}. "
        f"Use single characters (e.g. 'w') or aliases like UP/DOWN/LEFT/RIGHT/SPACE/CTRL_C, "
        f"or escapes like '\\x03'."
    )


def _as_key_list(v: Any, *, key: str, path: Path) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        items = [v]
    elif isinstance(v, list):
        items = v
    else:
        raise ValueError(
            f"Key {key!r} in {path} must be a string or list of strings; got {type(v).__name__}"
        )

    out: list[str] = []
    for it in items:
        if not isinstance(it, str):
            raise ValueError(
                f"Key {key!r} in {path} must contain only strings; got {type(it).__name__}"
            )
        out.append(_parse_key_token(it, key=key, path=path))
    return out


@dataclass(frozen=True, slots=True)
class TeleopKeymap:
    # quitting
    quit: list[str]

    # motor
    motor_forward: list[str]
    motor_backward: list[str]
    motor_left: list[str]
    motor_right: list[str]
    motor_stop: list[str]

    motor_fwd_left: list[str]
    motor_fwd_right: list[str]
    motor_back_left: list[str]
    motor_back_right: list[str]

    # servo
    servo_pan_left: list[str]
    servo_pan_right: list[str]
    servo_tilt_up: list[str]
    servo_tilt_down: list[str]
    servo_center: list[str]

    @staticmethod
    def defaults() -> "TeleopKeymap":
        # canonical fallback if YAML is missing/partial
        return TeleopKeymap(
            quit=["q", _KEY_ALIASES["CTRL_C"]],
            motor_forward=[_KEY_ALIASES["UP"]],
            motor_backward=[_KEY_ALIASES["DOWN"]],
            motor_left=[_KEY_ALIASES["LEFT"]],
            motor_right=[_KEY_ALIASES["RIGHT"]],
            motor_stop=[_KEY_ALIASES["SPACE"]],
            motor_fwd_left=["u"],
            motor_fwd_right=["o"],
            motor_back_left=["j"],
            motor_back_right=["l"],
            servo_pan_left=["a"],
            servo_pan_right=["d"],
            servo_tilt_up=["w"],
            servo_tilt_down=["s"],
            servo_center=["c"],
        )

    @staticmethod
    def from_mapping(data: Mapping[str, Any], *, path: Path) -> "TeleopKeymap":
        allowed = {
            "quit",
            "motor_forward",
            "motor_backward",
            "motor_left",
            "motor_right",
            "motor_stop",
            "motor_fwd_left",
            "motor_fwd_right",
            "motor_back_left",
            "motor_back_right",
            "servo_pan_left",
            "servo_pan_right",
            "servo_tilt_up",
            "servo_tilt_down",
            "servo_center",
        }
        forbid_unknown_keys(data, allowed, path=path)

        d = TeleopKeymap.defaults()

        return TeleopKeymap(
            quit=_as_key_list(data.get("quit", d.quit), key="quit", path=path),
            motor_forward=_as_key_list(
                data.get("motor_forward", d.motor_forward),
                key="motor_forward",
                path=path,
            ),
            motor_backward=_as_key_list(
                data.get("motor_backward", d.motor_backward),
                key="motor_backward",
                path=path,
            ),
            motor_left=_as_key_list(
                data.get("motor_left", d.motor_left), key="motor_left", path=path
            ),
            motor_right=_as_key_list(
                data.get("motor_right", d.motor_right), key="motor_right", path=path
            ),
            motor_stop=_as_key_list(
                data.get("motor_stop", d.motor_stop), key="motor_stop", path=path
            ),
            motor_fwd_left=_as_key_list(
                data.get("motor_fwd_left", d.motor_fwd_left),
                key="motor_fwd_left",
                path=path,
            ),
            motor_fwd_right=_as_key_list(
                data.get("motor_fwd_right", d.motor_fwd_right),
                key="motor_fwd_right",
                path=path,
            ),
            motor_back_left=_as_key_list(
                data.get("motor_back_left", d.motor_back_left),
                key="motor_back_left",
                path=path,
            ),
            motor_back_right=_as_key_list(
                data.get("motor_back_right", d.motor_back_right),
                key="motor_back_right",
                path=path,
            ),
            servo_pan_left=_as_key_list(
                data.get("servo_pan_left", d.servo_pan_left),
                key="servo_pan_left",
                path=path,
            ),
            servo_pan_right=_as_key_list(
                data.get("servo_pan_right", d.servo_pan_right),
                key="servo_pan_right",
                path=path,
            ),
            servo_tilt_up=_as_key_list(
                data.get("servo_tilt_up", d.servo_tilt_up),
                key="servo_tilt_up",
                path=path,
            ),
            servo_tilt_down=_as_key_list(
                data.get("servo_tilt_down", d.servo_tilt_down),
                key="servo_tilt_down",
                path=path,
            ),
            servo_center=_as_key_list(
                data.get("servo_center", d.servo_center),
                key="servo_center",
                path=path,
            ),
        )


@dataclass(frozen=True, slots=True)
class TeleopConfig:
    speed: int
    steer: int
    servo_step: int

    poll_s: float
    deadman_s: float

    invert_steer: bool
    invert_pan: bool
    invert_tilt: bool

    debug_keys: bool

    keymap: TeleopKeymap

    @staticmethod
    def defaults() -> "TeleopConfig":
        return TeleopConfig(
            speed=1500,
            steer=1500,
            servo_step=20,
            poll_s=0.02,
            deadman_s=0.15,
            invert_steer=False,
            invert_pan=False,
            invert_tilt=False,
            debug_keys=False,
            keymap=TeleopKeymap.defaults(),
        )

    @staticmethod
    def from_mapping(data: Mapping[str, Any], *, path: Path) -> "TeleopConfig":
        allowed = {
            "speed",
            "steer",
            "servo_step",
            "poll_s",
            "deadman_s",
            "invert_steer",
            "invert_pan",
            "invert_tilt",
            "debug_keys",
            "keymap",
        }
        forbid_unknown_keys(data, allowed, path=path)

        d = TeleopConfig.defaults()

        keymap_raw = data.get("keymap", None)
        if keymap_raw is None:
            keymap = d.keymap
        else:
            if not isinstance(keymap_raw, Mapping):
                raise ValueError(f"Key 'keymap' in {path} must be a mapping/object")
            keymap = TeleopKeymap.from_mapping(keymap_raw, path=path)

        return TeleopConfig(
            speed=as_int(data.get("speed", d.speed), key="speed", path=path),
            steer=as_int(data.get("steer", d.steer), key="steer", path=path),
            servo_step=as_int(
                data.get("servo_step", d.servo_step), key="servo_step", path=path
            ),
            poll_s=as_float(data.get("poll_s", d.poll_s), key="poll_s", path=path),
            deadman_s=as_float(
                data.get("deadman_s", d.deadman_s), key="deadman_s", path=path
            ),
            invert_steer=bool(data.get("invert_steer", d.invert_steer)),
            invert_pan=bool(data.get("invert_pan", d.invert_pan)),
            invert_tilt=bool(data.get("invert_tilt", d.invert_tilt)),
            debug_keys=bool(data.get("debug_keys", d.debug_keys)),
            keymap=keymap,
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

    # teleop
    keyboard: str | None = None
    teleop_cfg: str | None = None

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
            
            "keyboard",
            "teleop_cfg",
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
            keyboard=opt_nonempty_str("keyboard"),   
            teleop_cfg=opt_nonempty_str("teleop_cfg"),
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
        
        if cfg.keyboard is not None and cfg.keyboard not in ("usb", "terminal"):
            raise ValueError(
                f"Key 'keyboard' in {path} must be 'usb' or 'terminal'; got {cfg.keyboard!r}"
            )

        if cfg.teleop_cfg is not None and cfg.keyboard is None:
            cfg = RunConfig(**{**cfg.__dict__, "keyboard": "terminal"})

        if cfg.teleop_cfg is not None and cfg.motor_controller is None and cfg.servo_controller is None:
            raise ValueError(
                f"If 'teleop_cfg' is set in {path}, at least one of motor_controller/servo_controller must be set"
            )


        return cfg



