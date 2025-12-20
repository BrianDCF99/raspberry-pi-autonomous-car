from carbot.controllers.freenove.ultrasonic import Ultrasonics
from time import sleep

ult_ctl = Ultrasonics()

try:
    while True:
        distance = ult_ctl.get_distance()
        message = (
            f"Distance: {distance} cm"
            if distance is not None
            else "No Distance Measured"
        )
        print(message)
        sleep(0.5)

except KeyboardInterrupt:
    pass

finally:
    ult_ctl.close()
