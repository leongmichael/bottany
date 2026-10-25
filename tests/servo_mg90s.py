import sys
import time
from pathlib import Path

import pigpio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from constants import IN_S


# Servo signal pin is defined centrally in constants.py.
SERVO_PIN = IN_S

pi = pigpio.pi()
if not pi.connected:
    raise SystemExit("pigpio daemon not running. Start with: sudo systemctl start pigpiod")

def set_angle(angle: float):
    """
    Maps 0 to 180 degrees to standard MG90S pulse widths (500us - 2500us).
    """
    angle = max(0.0, min(180.0, angle))
    pulse_width = 500 + (angle / 180.0) * 2000
    pi.set_servo_pulsewidth(SERVO_PIN, pulse_width)

try:
    print("Testing MG90S Servo Sweep...")
    while True:
        for target in [0, 45, 90, 135, 180, 90]:
            print(f"Angle: {target}°")
            set_angle(target)
            time.sleep(1.0)

except KeyboardInterrupt:
    print("\nStopping...")
finally:
    # Set pulsewidth to 0 to disable signal and stop drawing holding current
    pi.set_servo_pulsewidth(SERVO_PIN, 0)
    pi.stop()
