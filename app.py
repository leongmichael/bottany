"""Flask dashboard for the Raspberry Pi plant light tracker."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template, request

from controller import PlantController

BASE_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = BASE_DIR / "settings.json"
DEFAULT_SETTINGS = {"time_per_side_minutes": 60.0}
MIN_INTERVAL_MINUTES = 0.1
MAX_INTERVAL_MINUTES = 10080.0


def load_settings() -> Dict[str, float]:
    try:
        data = json.loads(SETTINGS_PATH.read_text())
        minutes = float(data["time_per_side_minutes"])
        if MIN_INTERVAL_MINUTES <= minutes <= MAX_INTERVAL_MINUTES:
            return {"time_per_side_minutes": minutes}
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, float]) -> None:
    temporary_path = SETTINGS_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(settings, indent=2) + "\n")
    temporary_path.replace(SETTINGS_PATH)


def create_app(
    controller: Optional[PlantController] = None,
) -> Flask:
    app = Flask(__name__)
    settings = load_settings()
    if controller is None:
        mock_hardware = os.environ.get("BOTANY_MOCK_GPIO") == "1"
        controller = PlantController(
            interval_minutes=settings["time_per_side_minutes"],
            mock_hardware=mock_hardware,
        )
    app.extensions["plant_controller"] = controller

    @app.get("/")
    def dashboard() -> str:
        return render_template("index.html")

    @app.get("/api/status")
    def status() -> Any:
        return jsonify(controller.status())

    @app.post("/api/settings")
    def update_settings() -> Any:
        payload = request.get_json(silent=True) or {}
        raw_minutes = payload.get("time_per_side_minutes")

        if isinstance(raw_minutes, bool):
            return jsonify(error="Time per side must be a number"), 400

        try:
            minutes = float(raw_minutes)
        except (TypeError, ValueError):
            return jsonify(error="Time per side must be a number"), 400

        if not MIN_INTERVAL_MINUTES <= minutes <= MAX_INTERVAL_MINUTES:
            return jsonify(
                error=(
                    f"Time per side must be between {MIN_INTERVAL_MINUTES} "
                    f"and {MAX_INTERVAL_MINUTES:g} minutes"
                )
            ), 400

        new_settings = {"time_per_side_minutes": minutes}
        try:
            save_settings(new_settings)
        except OSError as exc:
            return jsonify(error=f"Could not save settings: {exc}"), 500

        controller.set_interval_minutes(minutes)
        return jsonify(ok=True, **new_settings)

    return app


app = create_app()


if __name__ == "__main__":
    hardware_controller = app.extensions["plant_controller"]
    try:
        hardware_controller.start()
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
    finally:
        hardware_controller.stop()
