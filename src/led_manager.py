import RPi.GPIO as GPIO
import io
import time
import logging


class LedManager:
    def __init__(self, config):
        led_pin = config["led_pin"]
        GPIO.setup(led_pin, GPIO.OUT)
        pass

    def turn_on_led(pin):
        GPIO.output(pin, GPIO.HIGH)

    def turn_off_led(pin):
        GPIO.output(pin, GPIO.LOW)

    def blink_led(self, pin):
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.5)
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(pin, GPIO.LOW)
        logging.info("LED blinked")
