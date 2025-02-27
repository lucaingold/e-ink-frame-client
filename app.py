from typing import Tuple, Optional, Dict, Any
import io
import threading
import time
import uuid
import logging
import paho.mqtt.client as mqtt
import json
from PIL import Image
import socket
from e_ink_screen import EInkScreen
from processed_message_tracker import ProcessedMessageTracker
from pijuice import PiJuice
import RPi.GPIO as GPIO  # Ensure this is the correct library
import atexit

# Constants
STATUS_ROOT = "data"
STATUS_POWER = "powerInput"
RECONNECT_DELAY = 5
LED_BLINK_DURATION = 0.5
DEFAULT_IP = '127.0.0.1'
IP_CHECK_ADDRESS = ('10.254.254.254', 1)
PIJUICE_ADDRESS = 0x14
PIJUICE_BUS = 1

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EInkFrameClient:
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.e_ink_screen_lock = threading.Lock()
        self.processed_message_tracker = ProcessedMessageTracker()
        self.e_ink_screen = None
        self.client = None
        self._setup_mqtt_client()
        self._setup_hardware()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            config["topic_device_status"] = self._get_status_topic(config)
            config["topic_image_display"] = self._get_display_topic(config)
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def _get_status_topic(self, config: Dict[str, Any]) -> str:
        return config["topic_device_status"].replace("{device_id}", config["device_id"])

    def _get_display_topic(self, config: Dict[str, Any]) -> str:
        return config["topic_image_display"].replace("{device_id}", config["device_id"])

    def _setup_hardware(self) -> None:
        try:
            self.e_ink_screen = EInkScreen(
                self.config["screen_width"],
                self.config["screen_height"]
            )
            self.e_ink_screen.run()
            GPIO.setup(self.config["led_pin"], GPIO.OUT)
        except Exception as e:
            logger.error(f"Failed to set up hardware: {e}")
            raise

    def _setup_mqtt_client(self) -> None:
        self.client = mqtt.Client(client_id=str(uuid.uuid4()), protocol=mqtt.MQTTv311)
        if self.config.get("password"):
            self.client.username_pw_set(
                self.config["username"],
                self.config["password"]
            )
            self.client.tls_set()

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # Configure Last Will and Testament
        lw_status = self._get_status_payload('offline')
        self.client.will_set(
            self.config["topic_device_status"],
            payload=lw_status,
            qos=1,
            retain=True
        )

    def _get_charge_status(self) -> Tuple[Optional[str], Optional[int]]:
        try:
            pijuice = PiJuice(PIJUICE_BUS, PIJUICE_ADDRESS)
            status = pijuice.status.GetStatus()[STATUS_ROOT][STATUS_POWER]
            charge_level = pijuice.status.GetChargeLevel()['data']
            logger.info(f'Status: {status}, Level: {charge_level}')
            return status, charge_level
        except Exception as e:
            logger.error(f'Error reading PiJuice status: {e}')
            return None, None

    def _blink_led(self) -> None:
        pin = self.config["led_pin"]
        for _ in range(2):
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(LED_BLINK_DURATION)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(LED_BLINK_DURATION)
        logger.info("LED blinked")

    def _get_ip(self) -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0)
            try:
                s.connect(IP_CHECK_ADDRESS)
                return s.getsockname()[0]
            except Exception as e:
                logger.warning(f"Failed to get IP: {e}")
                return DEFAULT_IP

    def _get_status_payload(self, status: str) -> str:
        power_status, battery_percentage = self._get_charge_status()
        return json.dumps({
            "hostname": socket.gethostname(),
            "ip_address": self._get_ip(),
            "mac": self.config["device_id"],
            'status': status,
            'wired': power_status == 'PRESENT',
            'battery': battery_percentage,
        })

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Dict, rc: int) -> None:
        logger.info(f"Connected with result code {rc}")
        client.subscribe(self.config["topic_image_display"])
        client.publish(
            self.config["topic_device_status"],
            payload=self._get_status_payload('online'),
            qos=1,
            retain=True
        )

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        logger.info(f"Received message on topic {msg.topic}")
        if msg.topic == self.config["topic_image_display"]:
            threading.Thread(target=self._process_image_message, args=(msg,)).start()

    def _process_image_message(self, msg: mqtt.MQTTMessage) -> None:
        try:
            if self.processed_message_tracker.should_process_message(msg.mid, msg.timestamp):
                img = Image.open(io.BytesIO(msg.payload))
                with self.e_ink_screen_lock:
                    self.e_ink_screen.display_image_on_epd(img)
                    self._blink_led()
                    time.sleep(5)
                    self.processed_message_tracker.mark_message_as_processed(msg.mid, msg.timestamp)
        except Exception as e:
            logger.error(f"Error processing image: {e}")

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
        logger.info("Disconnected from broker. Publishing offline status...")
        client.publish(
            self.config["topic_device_status"],
            payload=self._get_status_payload('offline'),
            qos=1,
            retain=True
        )
        time.sleep(RECONNECT_DELAY)
        client.reconnect()

    def run(self) -> None:
        try:
            self.client.connect(
                host=self.config["broker_address"],
                port=self.config["broker_port"],
                keepalive=30
            )
            self._blink_led()
            logger.info("E-Ink Frame Client started")
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self._on_disconnect(self.client, None, 0)
            GPIO.cleanup()

def main():
    client = EInkFrameClient()
    client.run()

if __name__ == "__main__":
    main()
