import os
import sys
import logging
import schedule
import threading
import time


class StatusScheduler:
    def __init__(self, config, battery_manager, mqtt_client_manager):
        self.should_shutdown_on_battery = config['should_shutdown_on_battery']
        self.battery_manager = battery_manager
        self.mqtt_client_manager = mqtt_client_manager
        self.schedule = schedule

    def publish_status_and_handle_shutdown(self):
        on_battery = self.battery_manager.is_on_battery()
        logging.info(f'Device is {"on battery." if on_battery else "wired."} ')
        if self.should_shutdown_on_battery and self.battery_manager.is_on_battery():
            self.battery_manager.prepare_shutdown()
            # But try to shut down nicely first
            # os.system("sudo shutdown -h 0")
            # sys.exit()
            logging.info(f'Shutting down...')
        else:
            self.mqtt_client_manager.send_status_msg('online')

    def run_scheduler(self):
        self.schedule.every(1).minutes.do(self.publish_status_and_handle_shutdown)
        while True:
            self.schedule.run_pending()
            time.sleep(1)

    def start(self):
        scheduler_thread = threading.Thread(target=self.run_scheduler)
        scheduler_thread.start()
