import io
import logging
import os
import time
from PIL import Image, ImageEnhance
from omni_epd import displayfactory, EPDNotFoundError

DISPLAY_TYPE = "waveshare_epd.it8951"

class EInkScreen:
    def __init__(self, screen_width=1600, screen_height=1200, brightness_factor=1.0, darkness_threshold=0.5):
        self.config_dict = {}
        self.epd = None
        self.width = screen_width
        self.height = screen_height
        self.brightness_factor = brightness_factor
        self.darkness_threshold = darkness_threshold

    async def run(self):
        logging.info("einkframe has started")
        try:
            self.epd = displayfactory.load_display_driver(DISPLAY_TYPE, self.config_dict)
            self.epd.width = self.width
            self.epd.height = self.height
            image_rotate = 0
            self.width, self.height = self.set_rotate(self.epd.width, self.epd.height, image_rotate)
        except EPDNotFoundError:
            logging.error(f"Couldn't find {DISPLAY_TYPE}")
            raise
        except KeyboardInterrupt:
            logging.info("ctrl + c:")
            raise
        except BaseException as e:
            logging.error(f"Error initializing e-ink screen: {e}")
            raise

    async def display_image(self, image_data):
        try:
            self.display_image_on_epd(image_data)
            time.sleep(5)
        except Exception as e:
            logging.error(f"Error decoding and displaying the image: {e}")

    def display_image_on_epd(self, display_image):
        logging.info("display_image_on_epd")
        try:
            image_file_path = "save/image.jpeg"
            if os.path.exists(image_file_path):
                os.remove(image_file_path)
                logging.info("Existing file removed: %s", image_file_path)
            display_image.save(image_file_path)
            logging.info("Image saved to disk: %s", image_file_path)

            image_display = self.enhance_brightness(display_image)

            logging.info("Prepare e-ink screen")
            self.epd.prepare()
            logging.info("Clear e-ink screen")
            self.epd.clear()
            logging.info("Display image on e-ink screen")
            self.epd.display(image_display)
            logging.info("Send e-ink screen to sleep")
            self.epd.sleep()
        except Exception as e:
            logging.error(f"Error displaying image on e-ink screen: {e}")

    def enhance_brightness(self, img):
        img_gray = img.convert('L')
        histogram = img_gray.histogram()
        pixels = sum(histogram)
        brightness = sum(index * value for index, value in enumerate(histogram)) / pixels

        if brightness < self.darkness_threshold:
            brightness_factor = self.adjust_brightness_factor(brightness)
            logging.info("Increase brightness by %s", str(brightness_factor))
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(self.brightness_factor)

        return img

    def adjust_brightness_factor(self, brightness):
        if brightness <= 100:
            return self.brightness_factor + 0.2
        elif 100 < brightness < 105:
            return self.brightness_factor
        else:
            return self.brightness_factor - 0.2

    @staticmethod
    def set_rotate(width, height, rotate=0):
        if (rotate / 90) % 2 == 1:
            temp = width
            width = height
            height = temp
        return width, height
