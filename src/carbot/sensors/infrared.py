from freenove.infrared import Infrared

class InfraredController:
    def __init__(self) -> None:
        self._infrared = Infrared()

    def close(self) -> None:
        self._infrared.close()
    
    # [0] -> left, [1] -> center, [2] -> right
    def read_channels(self) -> tuple[int, int, int]:
        return(
            self._infrared.read_one_infrared(1),
            self._infrared.read_one_infrared(2),
            self._infrared.read_one_infrared(3)
        )
      
    
