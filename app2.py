import RPi.GPIO as GPIO
import time

# Set the GPIO mode and pin number
GPIO.setmode(GPIO.BOARD)
switch_pin = 33  # Example GPIO pin (you can change it)

# Setup the GPIO pin for input
GPIO.setup(switch_pin, GPIO.IN)

try:
    while True:
        # Read the state of the switch
        switch_state = GPIO.input(switch_pin)

        # Determine the state of the switch
        if switch_state == GPIO.HIGH:
            print("Switch is ON")
        else:
            print("Switch is OFF")

        # Add a small delay to prevent excessive CPU usage
        time.sleep(1)

except KeyboardInterrupt:
    # Clean up GPIO on keyboard interrupt
    GPIO.cleanup()