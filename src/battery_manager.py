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
