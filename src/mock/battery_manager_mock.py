STATUS_ROOT = "data"
STATUS_POWER = "powerInput"


class BatteryManager:
    def __init__(self, config):
        pass

    def get_power_status(self):
        return 'NOT_PRESENT'

    def get_battery_status(self):
        return 'NORMAL'

    def get_charge_level(self):
        return 100

    def is_on_battery(self):
        return self.get_status() == 'NORMAL'

    def prepare_shutdown(self):
        pass
