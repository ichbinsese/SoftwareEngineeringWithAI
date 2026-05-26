class Battery:
    """Battery management class"""

    def __init__(self):
        """Initialize battery management"""
        from Implementation.Waveshare.MicroPython.waveshare_battery import inits       
        init()

    @property
    def percentage(self):
        """Get the current battery percentage"""
        from Implementation.Waveshare.MicroPython.waveshare_battery  import get_percentage

        return get_percentage()

    @property
    def voltage(self):
        """Get the current battery voltage in millivolts"""
        from Implementation.Waveshare.MicroPython.waveshare_battery  import get_voltage

        return get_voltage()

    def read(self):
        """read raw battery ADC value"""
        from Implementation.Waveshare.MicroPython.waveshare_battery  import read

        return read()
