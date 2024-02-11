from pijuice import PiJuice

STATUS_ROOT = "data"
STATUS_POWER = "powerInput"


class BatteryManager:
    def __init__(self, config):
        self.config = config
        self.pijuice = PiJuice(1, 0x14)

    def get_status(self):
        return self.pijuice.status.GetStatus()[STATUS_ROOT][STATUS_POWER]

    def get_charge_level(self):
        return self.pijuice.status.GetChargeLevel()[STATUS_ROOT]

    def is_on_battery(self):
        return self.get_status() != 'PRESENT'

    def prepare_shutdown(self):
        # Remove power to PiJuice MCU IO pins
        self.pijuice.power.SetSystemPowerSwitch(0)
        # In 5 seconds we are not so nice - Remove 5V power to RPi
        self.pijuice.power.SetPowerOff(8)
        # Enable wakeup alarm
        self.pijuice.rtcAlarm.SetWakeupEnabled(True)
