import base64
import io
import time

import paho.mqtt.client as mqtt
import json
from io import BytesIO
from PIL import Image
from e_ink_screen_mock import EInkScreen


# from e_ink_screen import EInkScreen

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribe to a topic upon successful connection
    client.subscribe(config["topic_image_display"])


# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    print("Received message on topic {}".format(msg.topic))
    print("Received message payload length:", len(msg.payload))
    if msg.topic == config["topic_image_display"]:
        try:
            image_data = msg.payload
            img = Image.open(io.BytesIO(image_data))
            e_ink_screen.display_image_on_epd(img)
        except Exception as e:
            print("Error decoding and displaying the image:", str(e))


# Callback when the client is disconnected from the broker
def on_disconnect(client, userdata, rc):
    print("Disconnected from the broker. Trying to reconnect...")
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

    e_ink_screen = EInkScreen(config["screen_width"], config["screen_height"])
    e_ink_screen = EInkScreen(config["screen_width"], config["screen_height"])
    e_ink_screen.run()

    client = mqtt.Client()

    # Set the callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    # Connect to the broker
    client.connect(config["broker_address"], config["broker_port"], 60)

    # Loop to maintain the connection and process incoming messages
    client.loop_forever()


if __name__ == "__main__":
    main()
