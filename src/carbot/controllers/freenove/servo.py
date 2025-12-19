from enum import StrEnum
from vendor.servo import Servo

PAN_MIN, PAN_MAX = 10, 170
TILT_MIN, TILT_MAX = 80, 180
MAX_TRIM = 10

PAN_HOME = 90
TILT_HOME = 90

# Implemented to overcome Freenove's Stringly Typed APIs
class ServoChannel(StrEnum):
    PAN = '0'
    TILT = '1'

class Servos:
    def __init__(self) -> None:
        self._servo = Servo()
        self._pan_trim = 0
        self._tilt_trim = 0

        self._curr_pan_angle: int
        self._curr_tilt_angle: int
        self.home()
    
    def close(self) -> None:
        self.home()
        self._servo.close()
    
    def home(self) -> None:
        self.set_pan_angle(PAN_HOME)
        self.set_tilt_angle(TILT_HOME)
    
    def set_pan_angle(self, requested_angle: int) -> None:
        self._set_angle(requested_angle, ServoChannel.PAN)

    def set_tilt_angle(self, requested_angle: int) -> None:
        self._set_angle(requested_angle, ServoChannel.TILT)
    
    def set_pan_trim(self, trim: int) -> None:
        self._pan_trim = max(-MAX_TRIM, min(MAX_TRIM, trim))

    def set_tilt_trim(self, trim: int) -> None:
        self._tilt_trim = max(-MAX_TRIM, min(MAX_TRIM, trim))
        
    @property
    def curr_pan_angle(self) -> int:
        return self._curr_pan_angle

    @property
    def curr_tilt_angle(self) -> int:
        return self._curr_tilt_angle
    
    # Clamp requested to get a logical angle
    # Trim physical offset and clamp again in case offset pushed over limit 
    def _set_angle(self, requested_angle: int, channel: ServoChannel) -> None:
        logical_angle = self._clamp(requested_angle, channel)
        new_angle = self._clamp(self._trim(logical_angle, channel), channel)
        self._servo.set_servo_pwm(channel.value, new_angle)

        if channel == ServoChannel.PAN:
            self._curr_pan_angle = logical_angle
        else:
            self._curr_tilt_angle = logical_angle

    def _trim(self, angle: int, channel: ServoChannel) -> int:
        trim = self._pan_trim if channel == ServoChannel.PAN else self._tilt_trim
        return angle + trim

    def _clamp(self, angle: int, channel: ServoChannel) -> int:
        max_angle = PAN_MAX if channel == ServoChannel.PAN else TILT_MAX
        min_angle = PAN_MIN if channel == ServoChannel.PAN else TILT_MIN
        if angle > max_angle:
            return max_angle
        if angle < min_angle:
            return min_angle
        return angle
     

