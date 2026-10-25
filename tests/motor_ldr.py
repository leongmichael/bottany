"""Run motor 1 forward while the active-low LDR on GPIO 6 is triggered."""

import sys
import time
from pathlib import Path

from gpiozero import DigitalInputDevice, OutputDevice, PWMOutputDevice

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from constants import ENA1, IN1, IN2, LDR2  # noqa: E402

SPEED = 1.0  # From 0.0 to 1.0


if __name__ == "__main__":
    ldr = DigitalInputDevice(LDR2, pull_up=None, active_state=False)
    enable = PWMOutputDevice(ENA1, initial_value=0)
    input_1 = OutputDevice(IN1, initial_value=False)
    input_2 = OutputDevice(IN2, initial_value=False)
    previous_state = None

    try:
        print(f"Motor runs while LDR on GPIO {LDR2} is triggered. Press Ctrl+C to stop.")
        input_1.on()
        input_2.off()

        while True:
            state = int(ldr.value)
            enable.value = SPEED if state == 1 else 0

            if state != previous_state:
                print(f"LDR={state}: motor {'running' if state == 1 else 'stopped'}")
                previous_state = state

            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nStopping")
    finally:
        enable.value = 0
        input_1.off()
        input_2.off()
        ldr.close()
        enable.close()
        input_1.close()
        input_2.close()
