import RPi.GPIO as GPIO
import time

# Set GPIO mode
GPIO.setmode(GPIO.BCM)

# Set pin number
button_pin = 16

# Set pin as input with pull-up resistor
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    while True:
        # Read the state of the button
        button_state = GPIO.input(button_pin)

        # Print the state of the button
        if button_state == GPIO.HIGH:
            print("Button is not pushed (off)")
        else:
            print("Button is pushed (on)")
        time.sleep(1)
except KeyboardInterrupt:
    # Clean up GPIO on exit
    GPIO.cleanup()