import os

DISPLAY_TYPE = "waveshare_epd.it8951"


# DISPLAY_TYPE = "omni_epd.mock"


class EInkScreen:
    def __init__(self, screen_width=1600, screen_height=1200, brightness_factor=1.0, darkness_threshold=0.5):
        pass

    def run(self):
        pass

    def load_config(self):
        pass

    @staticmethod
    def set_rotate(width, height, rotate=0):
        pass

    def display_image(self, image_data):
        pass

    def display_image_on_epd(self, display_image):
        return
