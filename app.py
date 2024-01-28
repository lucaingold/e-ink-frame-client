import io
import threading
import time
import uuid

import paho.mqtt.client as mqtt
import json
from PIL import Image
import socket
# from e_ink_screen_mock import EInkScreen
from e_ink_screen import EInkScreen
from processed_message_tracker import ProcessedMessageTracker
from pijuice import PiJuice

e_ink_screen_lock = threading.Lock()
processed_message_tracker = ProcessedMessageTracker()

STATUS_ROOT = "data"
STATUS_POWER = "powerInput"


def get_status_payload(status, battery_percentage=0):
    battery = 0
    wired = True
    if battery_percentage:
        wired = False
    hostname = socket.gethostname()
    ip_address = get_ip()
    return json.dumps({
        "hostname": hostname,
        "ip_address": ip_address,
        "mac": config["device_id"],
        'status': status,
        'wired': wired,
        'battery': battery,
    })


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
        pijuice = PiJuice(1, 0x14)
        power_status = pijuice.status.GetStatus()[STATUS_ROOT][STATUS_POWER]
        charge_level = pijuice.status.GetChargeLevel()['data']
        print(power_status)
        print(charge_level)
        return charge_level
        # instance.charge_level = PiJuiceHandler.get_charge_status(power_status, charge_level)
    except Exception as e:
        print(e)


def get_status_topic():
    device_id = config["device_id"]
    device_id_placeholder = config["device_id_placeholder"]
    status_topic = config["topic_device_status"].replace(device_id_placeholder, device_id)
    return status_topic


def get_display_topic():
    device_id = config["device_id"]
    device_id_placeholder = config["device_id_placeholder"]
    return config["topic_image_display"].replace(device_id_placeholder, device_id)


# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribe to a topic upon successful connection
    client.subscribe(config["topic_image_display"])
    print(f'Subscribed to {config["topic_image_display"]}')
    battery_percentage = get_charge_status()
    client.publish(config["topic_device_status"], payload=get_status_payload('online', battery_percentage), qos=1, retain=True)


# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    print("Received message on topic {}".format(msg.topic))
    if msg.topic == config["topic_image_display"]:
        try:
            if processed_message_tracker.should_process_message(msg.mid, msg.timestamp):
                image_data = msg.payload
                img = Image.open(io.BytesIO(image_data))
                with e_ink_screen_lock:
                    e_ink_screen.display_image_on_epd(img)
                    time.sleep(5)
        except Exception as e:
            print("Error decoding and displaying the image:", str(e))


# Callback when the client is disconnected from the broker
def on_disconnect(client, userdata, rc):
    print("Disconnected from the broker. Will publish offline status. Trying to reconnect...")
    client.publish(config["topic_device_status"], payload=get_status_payload('offline'), qos=1, retain=True)
    # Add a delay before attempting to reconnect
    time.sleep(5)
    client.reconnect()


def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


def main():
    global config
    global e_ink_screen
    config = load_config()
    config["topic_device_status"] = get_status_topic()
    config["topic_image_display"] = get_display_topic()

    e_ink_screen = EInkScreen(config["screen_width"], config["screen_height"])
    e_ink_screen.run()

    client = mqtt.Client(client_id=str(uuid.uuid4()))

    if (config["password"]):
        client.username_pw_set(config["username"], config["password"])
        client.tls_set()

    # Set the callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    # Configure Last Will and Testament
    lw_status = get_status_payload('offline')
    print(config["topic_device_status"])
    client.will_set(config["topic_device_status"], payload=lw_status, qos=1, retain=True)

    # Connect to the broker
    client.connect(host=config["broker_address"], port=config["broker_port"], keepalive=30)

    # Loop to maintain the connection and process incoming messages
    client.loop_forever()


if __name__ == "__main__":
    main()
