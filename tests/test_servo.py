from time import sleep
from carbot.actuators.servo import Servos

def sweep(move_fn, start: int, end: int, step: int, delay: float = 0.005) -> None:
    if step <= 0:
        raise ValueError("step must be > 0")

    step = step if end >= start else -step
    stop = end + (1 if step > 0 else -1)

    for angle in range(start, stop, step):
        move_fn(angle)
        sleep(delay)

servo_ctl = Servos()

try:
    for i in range(0,3):
        sweep(servo_ctl.set_pan_angle,  90, 150, step=1)
        sweep(servo_ctl.set_pan_angle, 150,  30, step=1)
        sweep(servo_ctl.set_pan_angle, 30, 90, step= 1)

        sweep(servo_ctl.set_tilt_angle, 90,  80, step=1)
        sweep(servo_ctl.set_tilt_angle, 80, 130, step=1)
        sweep(servo_ctl.set_tilt_angle, 130, 90, step=1)


    # servo_ctl.set_tilt_angle(80)
    # servo_ctl.set_pan_angle(30)
    # sleep(90)

    # servo_ctl.set_tilt_angle(80)
    # servo_ctl.set_pan_angle(160)
    # sleep(90)


except KeyboardInterrupt:
    pass

finally:
    servo_ctl.close()