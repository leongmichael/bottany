"""Monitor both digital LDR modules until Ctrl+C is pressed."""

import sys
import time
from pathlib import Path

from gpiozero import DigitalInputDevice

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from constants import LDR1, LDR2  # noqa: E402


if __name__ == "__main__":
    # The LDR modules provide their own pull-up resistors.
    sensors = [
        DigitalInputDevice(LDR1, pull_up=None),
        DigitalInputDevice(LDR2, pull_up=None),
    ]
    previous = [None, None]

    print("Monitoring LDRs; cover and uncover each sensor. Press Ctrl+C to stop.")

    try:
        while True:
            for index, sensor in enumerate(sensors):
                state = int(sensor.value)
                if state != previous[index]:
                    print(f"LDR{index + 1} (GPIO {sensor.pin.number}): {state}")
                    previous[index] = state
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nStopping LDR test")
    finally:
        for sensor in sensors:
            sensor.close()

