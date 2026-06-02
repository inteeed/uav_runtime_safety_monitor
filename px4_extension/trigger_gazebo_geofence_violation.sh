#!/usr/bin/env bash
set -euo pipefail

MODEL="${GAZEBO_MODEL:-iris}"
X="${X:-60}"
Y="${Y:-0}"
Z="${Z:-3}"
SAMPLES="${SAMPLES:-160}"
PERIOD_S="${PERIOD_S:-0.05}"

if ! command -v gz >/dev/null 2>&1; then
  echo "gz command not found. Run this from a terminal where Gazebo Classic is installed."
  exit 2
fi

echo "Applying Gazebo geofence disturbance to model '${MODEL}' at (${X}, ${Y}, ${Z})."
echo "This moves the Gazebo model, but PX4 may reject or correct the disturbance."
echo "For a guaranteed monitor-only violation, use px4_extension/inject_monitor_violation.sh geofence."

gz model -m "${MODEL}" -p || {
  echo "Could not read model '${MODEL}'. Make sure PX4 Gazebo Classic is running."
  exit 2
}

for _ in $(seq 1 "${SAMPLES}"); do
  gz model -m "${MODEL}" -x "${X}" -y "${Y}" -z "${Z}" >/dev/null
  sleep "${PERIOD_S}"
done

echo "Final Gazebo pose:"
gz model -m "${MODEL}" -p
