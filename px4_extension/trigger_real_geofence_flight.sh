#!/usr/bin/env bash
# Fly PX4 SITL past the geofence so the monitor detects a REAL telemetry
# violation (not an injected one). SITL / test-stand use only.
#
# Prerequisites (separate terminals, see docs/px4_live_demo.md):
#   - PX4 Gazebo Classic SITL running,
#   - Micro XRCE-DDS Agent running,
#   - the monitor stack running (run_px4_monitor_stack.sh).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROS_SETUP="${ROS_SETUP:-/opt/ros/${ROS_DISTRO:-foxy}/setup.bash}"
PX4_ROS2_WS_SETUP="${PX4_ROS2_WS_SETUP:-}"
TARGET_X="${TARGET_X:-60.0}"
TARGET_Y="${TARGET_Y:-0.0}"
ALTITUDE="${ALTITUDE:-5.0}"
HOLD_S="${HOLD_S:-30.0}"

source_setup() {
  set +u
  # shellcheck disable=SC1090
  source "$1"
  set -u
}

if [[ ! -f "${ROS_SETUP}" ]]; then
  echo "ROS setup file not found: ${ROS_SETUP}" >&2
  exit 2
fi
source_setup "${ROS_SETUP}"

if [[ -n "${PX4_ROS2_WS_SETUP}" ]]; then
  if [[ ! -f "${PX4_ROS2_WS_SETUP}" ]]; then
    echo "PX4_ROS2_WS_SETUP does not exist: ${PX4_ROS2_WS_SETUP}" >&2
    exit 2
  fi
  source_setup "${PX4_ROS2_WS_SETUP}"
fi

echo "Commanding PX4 offboard flight to (${TARGET_X}, ${TARGET_Y}) m, alt ${ALTITUDE} m."
echo "Watch the monitor stack / data/px4_live_events.csv for GEOFENCE_VIOLATION."
exec python3 "${SCRIPT_DIR}/fly_beyond_geofence.py" \
  --target-x "${TARGET_X}" \
  --target-y "${TARGET_Y}" \
  --altitude "${ALTITUDE}" \
  --hold "${HOLD_S}"
