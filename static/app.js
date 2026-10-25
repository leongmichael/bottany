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
    elements.timePerSide.value = status.interval_minutes;
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

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  elements.formMessage.className = "form-message";
  elements.formMessage.textContent = "Saving…";

  try {
    const response = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        time_per_side_minutes: Number(elements.timePerSide.value),
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "Could not save setting");
    }
    elements.timePerSide.value = result.time_per_side_minutes;
    elements.formMessage.textContent = "Rotation schedule saved.";
    await refreshStatus();
  } catch (error) {
    elements.formMessage.className = "form-message error";
    elements.formMessage.textContent = error.message;
  }
});

refreshStatus();
window.setInterval(refreshStatus, 1000);
