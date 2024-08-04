import io
import logging
import socket
import json
import time
from PIL import Image
from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI, Depends, HTTPException
import uvicorn
import paho.mqtt.client as mqtt
from src.config_loader import ConfigLoader
import io
import logging
import os
import time
from PIL import Image, ImageEnhance
from IT8951.display import AutoEPDDisplay
from IT8951 import constants

DISPLAY_TYPE = "waveshare_epd.it8951"

logging.basicConfig(level=logging.INFO)


def replace_device_id_placeholder(topic: str):
    return topic.replace(mqtt_config.device_id_placeholder, device_config.id)


def set_rotate(width, height, rotate=0):
    if (rotate / 90) % 2 == 1:
        temp = width
        width = height
        height = temp
    return width, height


config_loader = ConfigLoader()
app_config = config_loader.load()
mqtt_config = app_config.mqtt
device_config = app_config.device
screen_config = app_config.screen

mqtt_client = mqtt.Client()
status_topic = replace_device_id_placeholder(mqtt_config.topic_device_status)
image_topic = replace_device_id_placeholder(mqtt_config.topic_image_display)
config_dict = {}

print('Initializing EPD...')
display = AutoEPDDisplay(vcom=-2.27, rotate=None, mirror=None, spi_hz=24000000)
print('VCOM set to', display.epd.get_vcom())
epd = display.epd

print('System info:')
print('  display size: {}x{}'.format(epd.width, epd.height))
print('  img buffer address: {:X}'.format(epd.img_buf_address))
print('  firmware version: {}'.format(epd.firmware_version))
print('  LUT version: {}'.format(epd.lut_version))
print()
# epd.width = screen_config.width
# epd.height = screen_config.height
image_rotate = 0
# width, height = set_rotate(epd.width, epd.height, image_rotate)


def get_mqtt_client():
    return mqtt_client


async def publish_periodically(client: mqtt.Client):
    while True:
        await asyncio.sleep(60)
        client.publish(status_topic, get_status_payload("online"))


def get_status_payload(status):
    hostname = socket.gethostname()
    ip_address = get_ip()
    return json.dumps({
        "hostname": hostname,
        "ip_address": ip_address,
        "mac": device_config.id,
        'status': status,
        'wired': True,
        'battery': 100,
        'timestamp': time.time()
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


async def start_background_tasks():
    task = asyncio.create_task(publish_periodically(mqtt_client))
    return task


def display_image_on_epd(display_image):
    logging.info("display_image_on_epd")
    try:
        # image_file_path = "save/image.jpeg"
        # if os.path.exists(image_file_path):
        #     os.remove(image_file_path)
        #     logging.info("Existing file removed: %s", image_file_path)
        # display_image.save(image_file_path)
        # logging.info("Image saved to disk: %s", image_file_path)

        # image_display = self.enhance_brightness(display_image)

        logging.info("Prepare e-ink screen")
        logging.info("Clear e-ink screen")
        display.clear()
        logging.info("Display image on e-ink screen")
        display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))
        Image.open(display_image)
        dims = (display.width, display.height)
        display_image.thumbnail(dims)
        paste_coords = [dims[i] - display_image.size[i] for i in (0,1)]  # align image with bottom of display
        display.frame_buf.paste(display_image, paste_coords)
        display.draw_full(constants.DisplayModes.GC16)
        logging.info("Send e-ink screen to sleep")
        # epd.sleep()
        display.epd.sleep()
    except Exception as e:
        logging.error(f"Error displaying image on e-ink screen: {e}")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT Broker!")
    else:
        logging.error(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    logging.info(f"Received from `{msg.topic}` topic")
    image_data = Image.open(io.BytesIO(msg.payload))
    try:
        display_image_on_epd(image_data)
        time.sleep(5)
    except Exception as e:
        logging.error(f"Error decoding and displaying the image: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("lifespan start - startup")
    try:
        mqtt_client.username_pw_set(mqtt_config.username, mqtt_config.password)
        mqtt_client.tls_set()
        mqtt_client.connect(mqtt_config.broker, mqtt_config.port, 60)
        mqtt_client.on_message = on_message
        mqtt_client.on_connect = on_connect
        mqtt_client.loop_start()
        mqtt_client.subscribe(image_topic)
        logging.info("subscribed to image topic:" + image_topic)
        asyncio.create_task(start_background_tasks())
        yield
    except Exception as e:
        logging.error(f"Exception during lifespan: {e}")
        raise
    finally:
        logging.info("lifespan end - shutdown")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


app = FastAPI(lifespan=lifespan)


@app.get("/config")
async def root():
    app_config_without_password = app_config.copy()
    app_config_without_password.mqtt.password = "********"
    return app_config_without_password


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
