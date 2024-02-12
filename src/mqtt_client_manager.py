import paho.mqtt.client as mqtt
import uuid
import socket
import json
import time
import logging
import io
import threading
from PIL import Image

from src.processed_message_tracker import ProcessedMessageTracker

STATUS_ROOT = "data"
STATUS_POWER = "powerInput"
processed_message_tracker = ProcessedMessageTracker()
e_ink_screen_lock = threading.Lock()


class MQTTClientManager:
    def __init__(self, config, e_ink_screen, battery_manager):
        self.client = mqtt.Client(client_id=str(uuid.uuid4()))
        self.config = config
        self.battery_manager = battery_manager
        self.e_ink_screen = e_ink_screen
        if (config["password"]):
            self.client.username_pw_set(config["username"], config["password"])
            self.client.tls_set()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.will_set(config["topic_device_status"], payload=self.get_status_payload('offline'), qos=1,
                             retain=True)
        self.config = config

    def on_connect(self, client, userdata, flags, rc):
        logging.info("Connected with result code " + str(rc))
        client.subscribe(self.config["topic_image_display"])
        logging.info(f'Subscribed to {self.config["topic_image_display"]}')
        client.publish(self.config["topic_device_status"], payload=self.get_status_payload('online'), qos=1,
                       retain=True)

    def on_message(self, client, userdata, msg):
        logging.info("Received message on topic {}".format(msg.topic))
        if msg.topic == self.config["topic_image_display"]:
            try:
                if processed_message_tracker.should_process_message(msg.mid, msg.timestamp):
                    image_data = msg.payload
                    img = Image.open(io.BytesIO(image_data))
                    with e_ink_screen_lock:
                        self.e_ink_screen.display_image_on_epd(img)
                        time.sleep(5)
            except Exception as e:
                logging.error("Error decoding and displaying the image:", str(e))

    def send_status_msg(self, mqtt_status):
        self.client.publish(self.config["topic_device_status"], payload=self.get_status_payload(mqtt_status), qos=1,
                            retain=True)

    def on_disconnect(self, client, userdata, rc):
        logging.info("Disconnected from the broker. Will publish offline status. Trying to reconnect...")
        client.publish(self.config["topic_device_status"], payload=self.get_status_payload('offline'), qos=1,
                       retain=True)
        time.sleep(5)
        client.reconnect()

    def get_status_payload(self, status):
        power_status, battery_percentage = self.get_charge_status()
        wired = power_status == 'PRESENT'
        hostname = socket.gethostname()
        ip_address = self.get_ip()
        return json.dumps({
            "hostname": hostname,
            "ip_address": ip_address,
            "mac": self.config["device_id"],
            'status': status,
            'wired': wired,
            'battery': battery_percentage,
        })

    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def get_charge_status(self):
        try:
            power_status = self.battery_manager.get_status()
            charge_level = self.battery_manager.get_charge_level()
            logging.info(f'Status: {power_status}, Level: {charge_level}')
            return power_status, charge_level
        except Exception as e:
            logging.error(f'Error while reading pijuice status', e)
            return None, None

    def connect_to_broker(self):
        self.client.connect(host=self.config["broker_address"], port=self.config["broker_port"], keepalive=30)

    def start(self):
        mqtt_thread = threading.Thread(target=self.run_mqtt_client)
        mqtt_thread.start()

    def run_mqtt_client(self):
        self.connect_to_broker()

        client = mqtt.Client(client_id=str(uuid.uuid4()))

        if self.config["password"]:
            client.username_pw_set(self.config["username"], self.config["password"])
            client.tls_set()

        # atexit.register(shutdown_handler)

        # Configure Last Will and Testament
        lw_status = self.get_status_payload('offline')
        logging.info(self.config["topic_device_status"])
        client.will_set(self.config["topic_device_status"], payload=lw_status, qos=1, retain=True)

        # Connect to the broker
        client.connect(host=self.config["broker_address"], port=self.config["broker_port"], keepalive=30)

        self.client.loop_forever()
