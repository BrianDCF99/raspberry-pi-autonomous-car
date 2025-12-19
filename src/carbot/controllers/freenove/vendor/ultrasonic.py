from gpiozero import DistanceSensor, PWMSoftwareFallback, DistanceSensorNoEcho
import warnings


class Ultrasonic:
    def __init__(self, trigger_pin: int = 27, echo_pin: int = 22, max_distance: float = 3.0):
        # Initialize the Ultrasonic class and set up the distance sensor.
        warnings.filterwarnings("ignore", category = DistanceSensorNoEcho)
        warnings.filterwarnings("ignore", category = PWMSoftwareFallback)  # Ignore PWM software fallback warnings
        self.trigger_pin = trigger_pin  # Set the trigger pin number
        self.echo_pin = echo_pin        # Set the echo pin number
        self.max_distance: float = float(max_distance)  # Set the maximum distance
        self.sensor = DistanceSensor(
            echo=self.echo_pin,
            trigger=self.trigger_pin,
            max_distance=self.max_distance,  # type: ignore[arg-type]
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def get_distance(self) -> float | None:
        """
        Get the distance measurement from the ultrasonic sensor.

        Returns:
        float: The distance measurement in centimeters, rounded to one decimal place.
        """
        try:
            distance = self.sensor.distance * 100  # Get the distance in centimeters
            return round(float(distance), 1)  # Return the distance rounded to one decimal place
        except RuntimeWarning as e:
            print(f"Warning: {e}")
            return None

    def close(self):
        # Close the distance sensor.
        self.sensor.close()  # Close the sensor to release resources
