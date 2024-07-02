# config_loader.py
import yaml
from pydantic import BaseModel


class MQTTConfig(BaseModel):
    broker: str
    port: int
    username: str
    password: str
    device_id_placeholder: str
    topic_image_display: str
    topic_device_status: str


class DeviceConfig(BaseModel):
    id: str
    led_pin: int
    should_shutdown_on_battery: bool


class ScreenConfig(BaseModel):
    height: int
    width: int
    brightness_factor: float
    darkness_threshold: int


class Config(BaseModel):
    mqtt: MQTTConfig
    device: DeviceConfig
    screen: ScreenConfig


class ConfigLoader:
    @staticmethod
    def load(file_path="config.yaml"):
        with open(file_path, "r") as f:
            config_data = yaml.safe_load(f)
        return Config(
            mqtt=MQTTConfig(**config_data['mqtt']),
            device=DeviceConfig(**config_data['device']),
            screen=ScreenConfig(**config_data['screen'])
        )
