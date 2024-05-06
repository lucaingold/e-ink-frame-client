import io
import time
import uuid
import socket
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import logging
import json
from omni_epd import displayfactory, EPDNotFoundError

from PIL import Image

from src.battery_manager import BatteryManager
from src.e_ink_screen import EInkScreen

DISPLAY_TYPE = "waveshare_epd.it8951"

STATUS_ROOT = "data"
STATUS_POWER = "powerInput"
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

GPIO.setmode(GPIO.BCM)
button_pin = 16
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

turn_off_after_msg_consume = False


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


def on_connect(client, userdata, flags, rc):
    logging.info("Connected with result code " + str(rc))
    client.subscribe(config["topic_image_display"])
    logging.info(f'Subscribed to {config["topic_image_display"]}')
    client.publish(config["topic_device_status"], payload=get_status_payload('online'), qos=1,
                   retain=True)


def on_message(client, userdata, msg):
    logging.info("Received message on topic {}".format(msg.topic))
    if msg.topic == config["topic_image_display"]:
        try:
            image_data = msg.payload
            img = Image.open(io.BytesIO(image_data))
            show_image_on_screen(img)
            # retry = False
            time.sleep(5)
        except Exception as e:
            logging.error("Error decoding and displaying the image on message:", str(e))
            # if not retry:
            #     logging.error("Retry", str(e))
            #     time.sleep(3)
            #     retry = True
            #     on_message(None, None, msg)


def show_image_on_screen(display_image):
    try:
        image_display = display_image.copy()
        logging.info("Prepare e-ink screen")
        epd.prepare()
        logging.info("Clear e-ink screen")
        epd.clear()
        logging.info("Display image on e-ink screen")
        epd.display(image_display)
        logging.info("Send e-ink screen to sleep")
        epd.sleep()
        epd.close()
    except EPDNotFoundError:
        logging.error(f"Couldn't find {DISPLAY_TYPE}")
    except BaseException as e:
        logging.error(e)


def get_ip():
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


def get_charge_status():
    try:
        power_status = battery_manager.get_battery_status()
        charge_level = battery_manager.get_charge_level()
        logging.info(f'Status: {power_status}, Level: {charge_level}')
        return power_status, charge_level
    except Exception as e:
        logging.error(f'Error while reading pijuice status', e)
        return None, None


def get_status_payload( status):
    power_status, battery_percentage = get_charge_status()
    wired = power_status != 'NORMAL'
    hostname = socket.gethostname()
    ip_address = get_ip()
    return json.dumps({
        "hostname": hostname,
        "ip_address": ip_address,
        "mac": config["device_id"],
        'status': status,
        'wired': wired,
        'battery': battery_percentage,
        'timestamp': time.time()
    })

def set_rotate(width, height, rotate=0):
    if (rotate / 90) % 2 == 1:
        temp = width
        width = height
        height = temp
    return width, height


def main():
    try:
        global config
        global e_ink_screen
        global battery_manager
        global turn_off_after_msg_consume
        global width
        global height
        global epd
        image_rotate = 0


        button_state = GPIO.input(button_pin)
        config = load_config()
        config["topic_device_status"] = get_status_topic()
        config["topic_image_display"] = get_display_topic()
        width = config["screen_width"]
        height = config["screen_height"]
        epd = displayfactory.load_display_driver(DISPLAY_TYPE, {})
        epd.width = width
        epd.height = height
        width, height = set_rotate(epd.width, epd.height, image_rotate)

        if button_state == GPIO.HIGH:
            turn_off_after_msg_consume = False
        else:
            turn_off_after_msg_consume = True

        battery_manager = BatteryManager(config)

        # e_ink_screen = EInkScreen(config["screen_width"], config["screen_height"],
        #                           config["brightness_factor"], config["darkness_threshold"])
        # e_ink_screen.run()

        client = mqtt.Client(client_id=str(uuid.uuid4()))
        client.username_pw_set(config["username"], config["password"])
        client.tls_set()

        client.on_connect = on_connect
        client.on_message = on_message
        lw_status = get_status_payload('offline')
        client.will_set(config["topic_device_status"], payload=lw_status, qos=1, retain=True)

        client.connect(host=config["broker_address"], port=config["broker_port"], keepalive=30)
        client.loop_forever()

    except KeyboardInterrupt:
        # Clean up GPIO on exit
        GPIO.cleanup()


if __name__ == "__main__":
    main()