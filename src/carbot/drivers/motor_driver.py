from carbot.config.models import MotorConfig
from carbot.contracts.motor_controller import MotorController


class MotorDriver:
    def __init__(self, controller: MotorController, cfg: MotorConfig) -> None:
        self._controller = controller
        self._cfg = cfg

    def close(self) -> None:
        self.drive(0, 0)
        self._controller.close()

    ## Negative steer differential == Left Turn
    def drive(self, throttle: int, steer_differential: int) -> None:
        r_scale = self._cfg.right_scale if steer_differential != 0 else 1
        l_scale = self._cfg.left_scale if steer_differential != 0 else 1

        rpow = int(r_scale * (throttle + steer_differential))
        lpow = int(l_scale * (throttle - steer_differential))

        rpow = self._clamp(rpow)
        lpow = self._clamp(lpow)

        self._controller.set_wheels(lpow, lpow, rpow, rpow)

    def _clamp(self, power: int) -> int:
        max_pow = self._cfg.max_power
        return max(-max_pow, min(power, max_pow))
