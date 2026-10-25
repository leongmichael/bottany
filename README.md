# Plant Light Tracker

A Raspberry Pi light-following controller and web dashboard. Two digital LDR
modules steer an L298N-driven DC motor toward the active side, while an MG90S
servo rotates the plant 180 degrees on a configurable schedule.

## Behavior

- GPIO 6 active by itself: move right.
- GPIO 5 active by itself: move left.
- Both sensors equal: stop.
- The servo alternates between 0° and 180° after the configured time per side.
- The dashboard shows live sensors, motion, orientation, exposure time, and the
  countdown to the next turn.
- Rotation time can be entered in either minutes or seconds.

The LDR modules are treated as active-low. If their LEDs and dashboard values
behave in reverse, adjust each module's threshold potentiometer first.

## Wiring

The app uses BCM GPIO numbering from `constants.py`.

| Device | Signal | BCM GPIO |
| --- | --- | --- |
| L298N | ENA | 18 |
| L298N | IN1 | 27 |
| L298N | IN2 | 17 |
| Left LDR | Digital output | 5 |
| Right LDR | Digital output | 6 |
| MG90S | Signal | 12 |

Use an external supply suitable for the DC motor and a stable 5 V supply for
the servo. Connect the Raspberry Pi, L298N, servo supply, and sensor grounds
together. Do not power the DC motor from the Pi.

This configuration has no limit switches or movement timeout. If the sensor
state remains one-sided, the DC motor will continue running.

## Raspberry Pi setup

Install the system GPIO packages and start the pigpio daemon:

```bash
sudo apt update
sudo apt install python3-venv python3-gpiozero python3-pigpio pigpio
sudo systemctl enable --now pigpiod
```

From the project directory, create an environment that can access the GPIO
system packages and install the web dependency:

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Start the tracker:

```bash
python3 app.py
```

Find the Pi's local IP with `hostname -I`, then open
`http://PI_IP_ADDRESS:5000` from a device on the same network.

Press `Ctrl+C` to stop the app and release the GPIO devices.

## Dashboard-only mode

To view the dashboard without activating hardware:

```bash
BOTANY_MOCK_GPIO=1 python3 app.py
```

The dashboard setting is stored locally in `settings.json`.
