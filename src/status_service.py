import schedule
import threading
import time


class StatusScheduler:
    def __init__(self):
        self.schedule = schedule

    def publish_status(self):
        print("This method is called every one minute")

    def run_scheduler(self):
        self.schedule.every(1).minutes.do(self.publish_status)
        while True:
            self.schedule.run_pending()
            time.sleep(1)

    def start(self):
        scheduler_thread = threading.Thread(target=self.run_scheduler)
        scheduler_thread.start()
