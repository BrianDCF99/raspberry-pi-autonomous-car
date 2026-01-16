from __future__ import annotations

from dataclasses import dataclass

from carbot.config.models import RunConfig
from carbot.data.models import Metadata, MetadataBuilder
from carbot.drivers.camera_driver import CameraDriver
from carbot.drivers.infrared_driver import InfraredDriver
from carbot.drivers.motor_driver import MotorDriver
from carbot.drivers.servo_driver import ServoDriver
from carbot.drivers.ultrasonic_driver import UltrasonicDriver
from carbot.factories.builders.camera import build_camera_driver
from carbot.factories.builders.infrared import build_infrared_driver
from carbot.factories.builders.motor import build_motor_driver
from carbot.factories.builders.servo import build_servo_driver
from carbot.factories.builders.stream import build_streaming_service
from carbot.factories.builders.ultrasonic import build_ultrasonic_driver
from carbot.vision.stream_service import StreamingService
from carbot.factories.builders.teleop import build_teleop
from carbot.inputs.teleop import Teleop


@dataclass(slots=True)
class App:
    motor: MotorDriver | None = None
    servo: ServoDriver | None = None
    infrared: InfraredDriver | None = None
    ultrasonic: UltrasonicDriver | None = None
    camera: CameraDriver | None = None
    streaming: StreamingService | None = None
    teleop: Teleop | None = None
    meta: Metadata | None = None

    def close(self) -> None:
        # Close in reverse-ish dependency order
        if self.teleop is not None:
            self.teleop.close()
    
        if self.streaming is not None:
            self.streaming.close()

        if self.camera is not None:
            self.camera.close()

        if self.ultrasonic is not None:
            self.ultrasonic.close()

        if self.infrared is not None:
            self.infrared.close()

        if self.servo is not None:
            self.servo.close()

        if self.motor is not None:
            self.motor.close()


def build_app(run_cfg: RunConfig) -> App:
    app = App()
    md = MetadataBuilder()
    
    # Motor
    if run_cfg.motor_controller is not None:
        if run_cfg.motor_cfg is None:
            raise ValueError(
                "RunConfig: motor_cfg must be set when motor_controller is set"
            )
        app.motor = build_motor_driver(
            controller=run_cfg.motor_controller,
            cfg=run_cfg.motor_cfg,
        )

        md.set_motor_cfg(app.motor.cfg)

    # Servo
    if run_cfg.servo_controller is not None:
        if run_cfg.servo_cfg is None:
            raise ValueError(
                "RunConfig: servo_cfg must be set when servo_controller is set"
            )
        app.servo = build_servo_driver(
            controller=run_cfg.servo_controller,
            cfg=run_cfg.servo_cfg,
        )

        md.set_servo_cfg(app.servo.cfg)

    # Infrared
    if run_cfg.infrared_controller is not None:
        if run_cfg.infrared_cfg is None:
            raise ValueError(
                "RunConfig: infrared_cfg must be set when infrared_controller is set"
            )
        app.infrared = build_infrared_driver(
            controller=run_cfg.infrared_controller,
            cfg=run_cfg.infrared_cfg,
        )

        md.set_infra_cfg(app.infrared.cfg)

    # Ultrasonic
    if run_cfg.ultrasonic_controller is not None:
        if run_cfg.ultrasonic_cfg is None:
            raise ValueError(
                "RunConfig: ultrasonic_cfg must be set when ultrasonic_controller is set"
            )
        app.ultrasonic = build_ultrasonic_driver(
            controller=run_cfg.ultrasonic_controller,
            cfg=run_cfg.ultrasonic_cfg,
        )

        md.set_ultra_cfg(app.ultrasonic.cfg)


    # Camera (+ policy/config)
    if run_cfg.camera_controller is not None:
        if run_cfg.camera_cfg is None or run_cfg.camera_policy is None:
            raise ValueError(
                "RunConfig: camera_cfg and camera_policy must be set when camera_controller is set"
            )
        app.camera = build_camera_driver(
            controller=run_cfg.camera_controller,
            cfg=run_cfg.camera_cfg,
            policy=run_cfg.camera_policy,
        )

        md.set_cam_cfg(app.camera.cfg)
        md.set_cam_policy(app.camera.policy)
        app.camera.start()

    # Streaming depends on camera driver
    if run_cfg.networking is not None:
        if app.camera is None:
            raise ValueError(
                "RunConfig: networking requires camera_controller/camera_cfg/camera_policy"
            )
        app.streaming = build_streaming_service(
            camera_driver=app.camera,
            networking_cfg=run_cfg.networking,
        )

        md.set_network_cfg(app.streaming.cfg)
    
    # Teleop
    if run_cfg.teleop_cfg is not None:
        if app.motor is None and app.servo is None:
            raise ValueError("RunConfig: teleop_cfg requires motor_controller and/or servo_controller")

        keyboard = run_cfg.keyboard or "terminal"
        app.teleop = build_teleop(keyboard=keyboard, cfg_name_or_path=run_cfg.teleop_cfg)


    # Metadata
    app.meta = md.build()

    return app
