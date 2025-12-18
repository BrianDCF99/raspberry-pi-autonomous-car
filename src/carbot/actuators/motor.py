from freenove.motor import Ordinary_Car

# + / -  Testing Maximum
MAX_POWER = 2500



#TODO: forward, backward turning tuning to come back to same spot, same with for back
class Motors:
    def __init__(self) -> None:
        self._car = Ordinary_Car()

    def forward( self ) -> None:
        sp = 1500
        self.power_motor(sp, sp, sp, sp)

    def reverse( self ) -> None:
        sp = -1000
        self.power_motor(sp, sp, sp, sp)

    def inplace_right( self ) -> None:
        r_sp = -1400
        l_sp = 1600
        self.power_motor(l_sp, l_sp, r_sp, r_sp)

    def forward_right( self ) -> None:
        r_sp = 0
        l_sp = 2000
        self.power_motor(l_sp, l_sp, r_sp, r_sp)

    def reverse_right( self ) -> None:
        r_sp = 0
        l_sp = -2000
        self.power_motor(l_sp, l_sp, r_sp, r_sp)

    def inplace_left( self ) -> None:
        r_sp = 2000
        l_sp = -1550
        self.power_motor(l_sp, l_sp, r_sp, r_sp)

    def forward_left( self ) -> None:
        r_sp = 2000
        l_sp = 0
        self.power_motor(l_sp, l_sp, r_sp, r_sp)

    def reverse_left( self ) -> None:
        r_sp = -2000
        l_sp = 0
        self.power_motor(l_sp, l_sp, r_sp, r_sp)


    #Must get triggered after a couple seconds of no commands coming in
    def stop( self ) -> None:
        self.power_motor(0, 0, 0, 0)

    def _clamp( self, power: int) -> int:
        if power > MAX_POWER:
             return MAX_POWER
        if power < -MAX_POWER:
            return -MAX_POWER
        return power


    # Only function to talk to freenove
    # checks limits before sending command
    def power_motor( self,  front_left: int, back_left: int, front_right: int, back_right: int ) -> None:
        #TODO: Change to better ratios
       
        fl = self._clamp(front_left)
        bl = self._clamp(back_left)
        fr = self._clamp(front_right)
        br = self._clamp(back_right)

        self._car.set_motor_model(fl, bl, fr, br)

    def close( self ) -> None:
        self.stop()
        self._car.close()