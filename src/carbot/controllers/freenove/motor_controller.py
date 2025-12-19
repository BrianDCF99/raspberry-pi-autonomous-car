from carbot.contracts.motor_controller import MotorController
from .vendor.motor import Ordinary_Car

class FreenoveMotorController( MotorController ):
    def __init__( self ) -> None:
        self._motor = Ordinary_Car()
    
    def close( self ) -> None:
        self._motor.close()

    def set_wheels( self, fl: int, bl: int, fr: int, br: int ) -> None:
        self._motor.set_motor_model( fl, bl, fr, br )

