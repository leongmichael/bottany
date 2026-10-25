from gpiozero import DigitalInputDevice

# Module onboard 10k pull-up to 3.3V handles biasing
ldr_1 = DigitalInputDevice(17, pull_up=None)

