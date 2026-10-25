const elements = {
  connection: document.querySelector("#connection"),
  connectionText: document.querySelector("#connection-text"),
  exposureTime: document.querySelector("#exposure-time"),
  nextTurn: document.querySelector("#next-turn"),
  leftValue: document.querySelector("#left-value"),
  rightValue: document.querySelector("#right-value"),
  leftIndicator: document.querySelector("#left-indicator"),
  rightIndicator: document.querySelector("#right-indicator"),
  leftLight: document.querySelector("#left-light"),
  rightLight: document.querySelector("#right-light"),
  movement: document.querySelector("#movement"),
  servoAngle: document.querySelector("#servo-angle"),
  currentSide: document.querySelector("#current-side"),
  plant: document.querySelector("#plant"),
  hardwareError: document.querySelector("#hardware-error"),
  form: document.querySelector("#settings-form"),
  timePerSide: document.querySelector("#time-per-side"),
  timeUnit: document.querySelector("#time-unit"),
  formMessage: document.querySelector("#form-message"),
};

let settingLoaded = false;

function formatDuration(totalSeconds) {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
  }
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
}

function setActive(element, active) {
  element.classList.toggle("active", Boolean(active));
}

function setTimeInputUnit(unit, convertExisting = false) {
  const input = elements.timePerSide;
  const current = Number(input.value);

  if (convertExisting && Number.isFinite(current)) {
    input.value =
      unit === "seconds"
        ? Number((current * 60).toFixed(3))
        : Number((current / 60).toFixed(3));
  }

  if (unit === "seconds") {
    input.min = "1";
    input.max = "604800";
    input.step = "1";
  } else {
    input.min = "0.1";
    input.max = "10080";
    input.step = "0.1";
  }
}

function renderStatus(status) {
  elements.connection.className = "connection online";
  elements.connectionText.textContent =
    status.hardware_mode === "mock" ? "Mock mode" : "Tracker online";
  elements.exposureTime.textContent = formatDuration(status.exposure_seconds);
  elements.nextTurn.textContent = formatDuration(status.next_turn_seconds);
  elements.leftValue.textContent = status.left_ldr;
  elements.rightValue.textContent = status.right_ldr;
  elements.servoAngle.textContent = status.servo_angle;
  elements.currentSide.textContent = `${status.current_side.toUpperCase()} SIDE`;
  elements.plant.classList.toggle("back", status.servo_angle === 180);

  setActive(elements.leftIndicator, status.left_ldr);
  setActive(elements.rightIndicator, status.right_ldr);
  setActive(elements.leftLight, status.left_ldr);
  setActive(elements.rightLight, status.right_ldr);

  const directionLabels = {
    left: "← MOVING LEFT",
    right: "MOVING RIGHT →",
    stopped: "STOPPED",
  };
  elements.movement.textContent =
    directionLabels[status.motor_direction] || status.motor_direction;
  elements.movement.classList.toggle(
    "moving",
    status.motor_direction !== "stopped",
  );

  if (!settingLoaded) {
    if (status.interval_minutes < 0.1) {
      elements.timeUnit.value = "seconds";
      setTimeInputUnit("seconds");
      elements.timePerSide.value = Number(
        (status.interval_minutes * 60).toFixed(3),
      );
    } else {
      elements.timePerSide.value = Number(
        status.interval_minutes.toFixed(3),
      );
    }
    settingLoaded = true;
  }

  elements.hardwareError.hidden = !status.error;
  elements.hardwareError.textContent = status.error
    ? `Hardware stopped: ${status.error}`
    : "";
}

async function refreshStatus() {
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Status request failed (${response.status})`);
    }
    renderStatus(await response.json());
  } catch (error) {
    elements.connection.className = "connection offline";
    elements.connectionText.textContent = "Dashboard offline";
  }
}

elements.timeUnit.addEventListener("change", () => {
  setTimeInputUnit(elements.timeUnit.value, true);
});

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  elements.formMessage.className = "form-message";
  elements.formMessage.textContent = "Saving…";

  try {
    const enteredTime = Number(elements.timePerSide.value);
    const minutes =
      elements.timeUnit.value === "seconds" ? enteredTime / 60 : enteredTime;
    const response = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        time_per_side_minutes: minutes,
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "Could not save setting");
    }
    elements.formMessage.textContent = "Rotation schedule saved.";
    await refreshStatus();
  } catch (error) {
    elements.formMessage.className = "form-message error";
    elements.formMessage.textContent = error.message;
  }
});

refreshStatus();
window.setInterval(refreshStatus, 1000);
