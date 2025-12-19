from carbot.controllers.freenove.infrared import InfraredController
from time import sleep

infr_ctl = InfraredController()

try:
    while True:
        print(infr_ctl.read_channels())
        sleep(0.3)

except KeyboardInterrupt:
    pass

finally:
    infr_ctl.close()
