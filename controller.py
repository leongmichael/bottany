"""Hardware controller for the plant light tracker."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional

from constants import ENA1, IN1, IN2, IN_S, LDR1, LDR2


class PlantController:
    """Read the LDRs, steer the DC motor, and periodically turn the servo."""

    def __init__(
        self,
        interval_minutes: float,
        motor_speed: float = 1.0,
        mock_hardware: bool = False,
    ) -> None:
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._interval_seconds = interval_minutes * 60
        self._motor_speed = motor_speed
        self._mock_hardware = mock_hardware
        self._started_at = time.monotonic()
        self._last_turn = self._started_at
        self._left_active = False
        self._right_active = False
        self._motor_direction = "stopped"
        self._servo_angle = 0
        self._error: Optional[str] = None

        self._left_ldr: Any = None
        self._right_ldr: Any = None
        self._enable: Any = None
        self._input_1: Any = None
        self._input_2: Any = None
        self._pi: Any = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        if not self._mock_hardware:
            self._setup_hardware()

        self._stop_event.clear()
        self._started_at = time.monotonic()
        self._last_turn = self._started_at
        self._thread = threading.Thread(
            target=self._run,
            name="plant-controller",
            daemon=True,
        )
        self._thread.start()

    def _setup_hardware(self) -> None:
        try:
            import pigpio
            from gpiozero import DigitalInputDevice, OutputDevice, PWMOutputDevice

            # These digital LDR modules pull LOW when their threshold is reached.
            self._left_ldr = DigitalInputDevice(
                LDR1, pull_up=None, active_state=False
            )
            self._right_ldr = DigitalInputDevice(
                LDR2, pull_up=None, active_state=False
            )
            self._enable = PWMOutputDevice(ENA1, initial_value=0)
            self._input_1 = OutputDevice(IN1, initial_value=False)
            self._input_2 = OutputDevice(IN2, initial_value=False)

            self._pi = pigpio.pi()
            if not self._pi.connected:
                raise RuntimeError(
                    "pigpio daemon is not running; start it with "
                    "'sudo systemctl start pigpiod'"
                )
            self._set_servo_angle(0)
        except Exception:
            self._close_hardware()
            raise

    def _run(self) -> None:
        try:
            while not self._stop_event.wait(0.05):
                if self._mock_hardware:
                    with self._lock:
                        left = self._left_active
                        right = self._right_active
                else:
                    left = bool(self._left_ldr.value)
                    right = bool(self._right_ldr.value)

                direction = self._direction_for(left, right)
                self._drive_motor(direction)

                now = time.monotonic()
                with self._lock:
                    self._left_active = left
                    self._right_active = right
                    interval = self._interval_seconds
                    should_turn = now - self._last_turn >= interval

                if should_turn:
                    self._turn_plant(now)
        except Exception as exc:
            with self._lock:
                self._error = str(exc)
            self._stop_motor()

    @staticmethod
    def _direction_for(left: bool, right: bool) -> str:
        if right and not left:
            return "right"
        if left and not right:
            return "left"
        return "stopped"

    def _drive_motor(self, direction: str) -> None:
        with self._lock:
            previous = self._motor_direction

        if direction == previous:
            return

        if not self._mock_hardware:
            # Stop before reversing to avoid abrupt direction changes.
            self._enable.value = 0
            self._input_1.off()
            self._input_2.off()

            if direction == "right":
                self._input_1.on()
                self._input_2.off()
                self._enable.value = self._motor_speed
            elif direction == "left":
                self._input_1.off()
                self._input_2.on()
                self._enable.value = self._motor_speed

        with self._lock:
            self._motor_direction = direction

    def _stop_motor(self) -> None:
        if not self._mock_hardware and self._enable is not None:
            self._enable.value = 0
            self._input_1.off()
            self._input_2.off()
        with self._lock:
            self._motor_direction = "stopped"

    def _turn_plant(self, now: float) -> None:
        with self._lock:
            new_angle = 180 if self._servo_angle == 0 else 0

        if not self._mock_hardware:
            self._set_servo_angle(new_angle)

        with self._lock:
            self._servo_angle = new_angle
            self._last_turn = now

    def _set_servo_angle(self, angle: int) -> None:
        pulse_width = 500 + (angle / 180.0) * 2000
        self._pi.set_servo_pulsewidth(IN_S, pulse_width)

    def set_interval_minutes(self, minutes: float) -> None:
        if minutes <= 0:
            raise ValueError("Time per side must be greater than zero")
        with self._lock:
            self._interval_seconds = minutes * 60

    def set_mock_sensors(self, left: bool, right: bool) -> None:
        """Set simulated sensor values for local verification."""
        if not self._mock_hardware:
            raise RuntimeError("Mock sensors are only available in mock mode")
        with self._lock:
            self._left_active = left
            self._right_active = right

    def status(self) -> Dict[str, Any]:
        now = time.monotonic()
        with self._lock:
            elapsed = max(0.0, now - self._last_turn)
            remaining = max(0.0, self._interval_seconds - elapsed)
            return {
                "left_ldr": int(self._left_active),
                "right_ldr": int(self._right_active),
                "motor_direction": self._motor_direction,
                "servo_angle": self._servo_angle,
                "current_side": "front" if self._servo_angle == 0 else "back",
                "exposure_seconds": round(elapsed, 1),
                "next_turn_seconds": round(remaining, 1),
                "interval_minutes": self._interval_seconds / 60,
                "uptime_seconds": round(max(0.0, now - self._started_at), 1),
                "hardware_mode": "mock" if self._mock_hardware else "raspberry-pi",
                "error": self._error,
            }

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._stop_motor()
        self._close_hardware()

    def _close_hardware(self) -> None:
        if self._pi is not None:
            self._pi.set_servo_pulsewidth(IN_S, 0)
            self._pi.stop()
            self._pi = None

        for device_name in (
            "_left_ldr",
            "_right_ldr",
            "_enable",
            "_input_1",
            "_input_2",
        ):
            device = getattr(self, device_name)
            if device is not None:
                device.close()
                setattr(self, device_name, None)
