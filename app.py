import io
import os
import sys
import uuid
import paho.mqtt.client as mqtt
import json
from PIL import Image
import socket
# from src.mock.e_ink_screen_mock import EInkScreen
from src.e_ink_screen import EInkScreen
# from src.mock.battery_manager_mock import BatteryManager
from src.battery_manager import BatteryManager
from src.mqtt_client_manager import MQTTClientManager
from src.processed_message_tracker import ProcessedMessageTracker
import atexit
import time
import threading
import logging

from src.status_service import StatusScheduler

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
e_ink_screen_lock = threading.Lock()
processed_message_tracker = ProcessedMessageTracker()

STATUS_ROOT = "data"
STATUS_POWER = "powerInput"


def get_status_topic():
    device_id = config["device_id"]
    device_id_placeholder = config["device_id_placeholder"]
    status_topic = config["topic_device_status"].replace(device_id_placeholder, device_id)
    return status_topic


def get_display_topic():
    device_id = config["device_id"]
    device_id_placeholder = config["device_id_placeholder"]
    return config["topic_image_display"].replace(device_id_placeholder, device_id)


def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


# def shutdown_handler():
#     client.publish(config["topic_device_status"], payload=get_status_payload('offline'), qos=1, retain=True)
#     logging.info("Shutting down gracefully...")


def safe_pijuice_shutdown():
    # Remove power to PiJuice MCU IO pins
    pijuice.power.SetSystemPowerSwitch(0)
    # In 5 seconds we are not so nice - Remove 5V power to RPi
    pijuice.power.SetPowerOff(5)
    # Enable wakeup alarm
    pijuice.rtcAlarm.SetWakeupEnabled(True)
    # But try to shut down nicely first
    os.system("sudo shutdown -h 0")
    sys.exit()


def main():
    try:
        global config
        global e_ink_screen
        global client
        global pijuice
        config = load_config()
        config["topic_device_status"] = get_status_topic()
        config["topic_image_display"] = get_display_topic()

        e_ink_screen = EInkScreen(config["screen_width"], config["screen_height"])
        e_ink_screen.run()

        battery_manager = BatteryManager(config)
        mqtt_client_manager = MQTTClientManager(config, e_ink_screen, battery_manager)
        mqtt_client_manager.start()

        status_publisher = StatusScheduler()
        status_publisher.start()

        logging.info("Started")

    except KeyboardInterrupt:
        pass
    finally:
        # shutdown_handler()
        pass


if __name__ == "__main__":
    main()
