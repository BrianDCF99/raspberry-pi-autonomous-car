from time import sleep
from carbot.hardware.actuators.motor import Motors



motors = Motors()

try:
    motors.forward()
    sleep(1)
    motors.reverse()
    sleep(1)
    motors.inplace_left()
    sleep(1)
    motors.inplace_right()
    sleep(1)
    motors.forward_right()
    sleep(1)
    motors.reverse_right()
    sleep(1)
    motors.forward_left()
    sleep(1)
    motors.reverse_left()
    sleep(1)
finally:
    motors.close()

