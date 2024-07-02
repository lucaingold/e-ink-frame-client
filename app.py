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
from src.e_ink_screen import EInkScreen

logging.basicConfig(level=logging.INFO)

config_loader = ConfigLoader()
app_config = config_loader.load()
mqtt_config = app_config.mqtt
device_config = app_config.device
screen_config = app_config.screen

mqtt_client = mqtt.Client()
status_topic = mqtt_config.topic_device_status
image_topic = mqtt_config.topic_image_display

eink_screen = EInkScreen()


async def initialize_eink():
    await eink_screen.run()


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


async def display_image_async(image_data):
    logging.info("display_image_async")
    await eink_screen.display_image(image_data)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT Broker!")
    else:
        logging.error(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    logging.info(f"Received from `{msg.topic}` topic")
    image_data = Image.open(io.BytesIO(msg.payload))
    # asyncio.create_task(display_image_async(image_data))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("lifespan start - startup")
    try:
        await initialize_eink()
        mqtt_client.username_pw_set(mqtt_config.username, mqtt_config.password)
        mqtt_client.tls_set()
        mqtt_client.connect(mqtt_config.broker, mqtt_config.port, 60)
        mqtt_client.on_message = on_message
        mqtt_client.on_connect = on_connect
        mqtt_client.loop_start()
        mqtt_client.subscribe(image_topic)
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
