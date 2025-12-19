from gpiozero import LineSensor

class Infrared:
    def __init__(self):
        self.IR_PINS = {
            1: 14,
            2: 15,
            3: 23
        }
        self.sensors = {channel: LineSensor(pin) for channel, pin in self.IR_PINS.items()}

    def read_one_infrared(self, channel: int) -> int:
        if channel in self.sensors:
            return 1 if self.sensors[channel].value else 0
        else:
            raise ValueError(f"Invalid channel: {channel}. Valid channels are {list(self.IR_PINS.keys())}.")

    def read_all_infrared(self) -> int:
        #Combine the values of all three infrared sensors into a single integer
        return (self.read_one_infrared(1) << 2) | (self.read_one_infrared(2) << 1) | self.read_one_infrared(3)

    def close(self) -> None:
        for sensor in self.sensors.values():
            sensor.close()
