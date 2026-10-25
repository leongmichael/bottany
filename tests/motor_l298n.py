"""Run motor 1 through an L298N driver until the program is stopped.

Run from the project root:
    python3 tests/motor_l298n.py
"""

import sys
import time
from pathlib import Path

from gpiozero import OutputDevice, PWMOutputDevice

# Allow this file to be run directly while keeping GPIO assignments centralized.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from constants import ENA1, IN1, IN2  # noqa: E402

SPEED = 0.5  # From 0.0 to 1.0


if __name__ == "__main__":
    enable = PWMOutputDevice(ENA1, initial_value=0)
    input_1 = OutputDevice(IN1, initial_value=False)
    input_2 = OutputDevice(IN2, initial_value=False)

    try:
        print(f"Running forward at {SPEED:.0%}; press Ctrl+C to stop")
        input_1.on()
        input_2.off()
        enable.value = SPEED
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping motor")
    finally:
        enable.value = 0
        input_1.off()
        input_2.off()
        enable.close()
        input_1.close()
        input_2.close()
