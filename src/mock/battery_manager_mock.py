STATUS_ROOT = "data"
STATUS_POWER = "powerInput"


class BatteryManager:
    def __init__(self, config):
        pass

    def get_status(self):
        return 'PRESENT'

    def get_charge_level(self):
        return 100
