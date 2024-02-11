STATUS_ROOT = "data"
STATUS_POWER = "powerInput"


class BatteryManager:
    def __init__(self, config):
        pass

    def get_status(self):
        return 'NOT_PRESENT'

    def get_charge_level(self):
        return 100

    def is_on_battery(self):
        return self.get_status() != 'PRESENT'

    def prepare_shutdown(self):
        pass
