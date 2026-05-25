#!/usr/bin/env bash

set -eo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="$PROJECT_ROOT/gazebo_extension/run_gui_demo.sh"
ROS_SETUP="${ROS_SETUP:-/opt/ros/foxy/setup.bash}"
SCENARIO="${1:-geofence_violation}"
COMMANDER_RUNTIME_S="${COMMANDER_RUNTIME_S:-45}"
LOG_ROOT="${LOG_ROOT:-$PROJECT_ROOT/results/gazebo_gui_logs}"
RUN_ID="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="$LOG_ROOT/$RUN_ID"

if [[ ! -f "$ROS_SETUP" ]]; then
  echo "ROS setup file not found: $ROS_SETUP" >&2
  exit 1
fi

dirty_environment=false

if [[ -n "${ROS_DISTRO:-}" && "${ROS_DISTRO}" != "foxy" ]]; then
  dirty_environment=true
fi

for env_var in ROS_PACKAGE_PATH CMAKE_PREFIX_PATH PYTHONPATH LD_LIBRARY_PATH GAZEBO_PLUGIN_PATH AMENT_PREFIX_PATH; do
  if [[ "${!env_var:-}" == *"/opt/ros/noetic"* ]]; then
    dirty_environment=true
  fi
done

if [[ "$dirty_environment" == "true" && "${UAV_DEMO_CLEAN_ENV:-0}" != "1" ]]; then
  echo "Detected an existing ROS/Noetic environment. Restarting with a clean ROS2 environment..."
  clean_env=(
    "UAV_DEMO_CLEAN_ENV=1"
    "HOME=${HOME:-/home/inteed}"
    "USER=${USER:-inteed}"
    "LOGNAME=${LOGNAME:-${USER:-inteed}}"
    "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    "ROS_SETUP=$ROS_SETUP"
    "COMMANDER_RUNTIME_S=$COMMANDER_RUNTIME_S"
    "LOG_ROOT=$LOG_ROOT"
  )

  for env_var in SHELL TERM LANG LC_ALL DISPLAY WAYLAND_DISPLAY XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS XAUTHORITY PULSE_SERVER LIBGL_ALWAYS_SOFTWARE; do
    if [[ -n "${!env_var:-}" ]]; then
      clean_env+=("$env_var=${!env_var}")
    fi
  done

  exec env -i "${clean_env[@]}" bash "$SCRIPT_PATH" "$@"
fi

if [[ "$dirty_environment" == "true" ]]; then
  echo "Current shell still contains ROS/Noetic paths after clean relaunch." >&2
  echo "Open a clean terminal before running the Gazebo/ROS2 GUI demo." >&2
  exit 2
fi

if [[ -z "${DISPLAY:-}" ]]; then
  echo "DISPLAY is not set. Gazebo GUI may not open from this terminal." >&2
fi

# ROS setup scripts can reference unset variables, so enable strict unset
# checking only after sourcing ROS.
source "$ROS_SETUP"
set -u

mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

export GAZEBO_MODEL_PATH="$PROJECT_ROOT/gazebo_extension/models:${GAZEBO_MODEL_PATH:-}"
export PYTHONUNBUFFERED=1

pids=()
cleanup() {
  for pid in "${pids[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait "${pids[@]:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Gazebo GUI demo"
echo "  scenario: $SCENARIO"
echo "  logs: $LOG_DIR"
echo
echo "Opening Gazebo Classic GUI..."

gazebo --verbose gazebo_extension/worlds/uav_safety_demo.world \
  >"$LOG_DIR/gazebo.log" 2>&1 &
gazebo_pid="$!"
pids+=("$gazebo_pid")

sleep 8

if ! kill -0 "$gazebo_pid" 2>/dev/null; then
  echo "Gazebo exited before the ROS2 nodes started. Recent Gazebo log:" >&2
  tail -n 40 "$LOG_DIR/gazebo.log" >&2 || true
  exit 3
fi

python3 gazebo_extension/gazebo_state_bridge_node.py \
  >"$LOG_DIR/bridge.log" 2>&1 &
pids+=("$!")

python3 ros2_extension/safety_monitor_node.py \
  >"$LOG_DIR/safety_monitor.log" 2>&1 &
pids+=("$!")

python3 ros2_extension/mission_supervisor_node.py \
  >"$LOG_DIR/mission_supervisor.log" 2>&1 &
pids+=("$!")

sleep 3

timeout "${COMMANDER_RUNTIME_S}s" python3 \
  gazebo_extension/gazebo_mission_commander_node.py \
  --ros-args -p scenario:="$SCENARIO" \
  >"$LOG_DIR/mission_commander.log" 2>&1 || true

echo
echo "Commander summary"
grep "Inserted supervisor response" "$LOG_DIR/mission_commander.log" || true
grep -E "command RESPONSE|command WAYPOINT_2" \
  "$LOG_DIR/mission_commander.log" | tail -n 20 || true

echo
echo "Monitor summary"
grep -E "GEOFENCE|ALTITUDE|LOW_BATTERY|MISSION_TIMEOUT|STATE_TIMEOUT" \
  "$LOG_DIR/safety_monitor.log" | head -n 20 || true

echo
echo "Supervisor summary"
grep -E "RETURNING_HOME|LANDING|MISSION_ABORTED|WARNING_ACTIVE" \
  "$LOG_DIR/mission_supervisor.log" | head -n 20 || true

echo
echo "Gazebo diagnostics"
if grep -E "Failed to load plugin|incorrect plugin" "$LOG_DIR/gazebo.log"; then
  echo "Gazebo plugin loading reported errors. Check $LOG_DIR/gazebo.log"
else
  echo "No Gazebo ROS plugin loading errors found."
fi

echo
echo "Gazebo should remain visible. Press Ctrl+C here to stop Gazebo and ROS2 nodes."
wait "$gazebo_pid"
