import RPi.GPIO as GPIO

# Set up GPIO using BCM numbering
GPIO.setmode(GPIO.BCM)

# Define the GPIO pin connected to the switch
switch_pin = 16

# Set up the switch pin as input
GPIO.setup(switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Read the initial state of the switch
switch_state = GPIO.input(switch_pin)

# Check if the switch is on or off
if switch_state == GPIO.HIGH:
    print("Switch is OFF")
else:
    print("Switch is ON")

# Clean up GPIO
GPIO.cleanup()