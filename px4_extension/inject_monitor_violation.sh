#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROS_SETUP="${ROS_SETUP:-/opt/ros/foxy/setup.bash}"
PX4_ROS2_WS_SETUP="${PX4_ROS2_WS_SETUP:-}"
SCENARIO="${1:-${SCENARIO:-geofence}}"
DURATION_S="${DURATION_S:-6.0}"
PUBLISH_PERIOD_S="${PUBLISH_PERIOD_S:-0.05}"

if [[ "${UAV_MONITOR_INJECT_CLEAN_ENV_DONE:-}" != "1" ]]; then
  if env | grep -E '^(ROS_PACKAGE_PATH|CMAKE_PREFIX_PATH|PYTHONPATH|LD_LIBRARY_PATH|PATH)=' | grep -q '/noetic' || [[ "${ROS_DISTRO:-}" == "noetic" ]]; then
    echo "Current shell contains ROS Noetic paths. Restarting the injection tool in a clean ROS2 environment."
    exec env -i \
      HOME="${HOME}" \
      USER="${USER:-}" \
      LOGNAME="${LOGNAME:-}" \
      PATH="${HOME}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
      ROS_SETUP="${ROS_SETUP}" \
      PX4_ROS2_WS_SETUP="${PX4_ROS2_WS_SETUP}" \
      SCENARIO="${SCENARIO}" \
      DURATION_S="${DURATION_S}" \
      PUBLISH_PERIOD_S="${PUBLISH_PERIOD_S}" \
      UAV_MONITOR_INJECT_CLEAN_ENV_DONE=1 \
      bash "${BASH_SOURCE[0]}" "$@"
  fi
fi

source_setup() {
  local setup_file="$1"
  set +u
  source "${setup_file}"
  set -u
}

if [[ ! -f "${ROS_SETUP}" ]]; then
  echo "ROS setup file not found: ${ROS_SETUP}"
  exit 2
fi

source_setup "${ROS_SETUP}"

if [[ -n "${PX4_ROS2_WS_SETUP}" ]]; then
  if [[ ! -f "${PX4_ROS2_WS_SETUP}" ]]; then
    echo "PX4_ROS2_WS_SETUP does not exist: ${PX4_ROS2_WS_SETUP}"
    exit 2
  fi
  source_setup "${PX4_ROS2_WS_SETUP}"
fi

if [[ ! -f "${REPO_ROOT}/install/setup.bash" ]]; then
  echo "ROS2 package install not found: ${REPO_ROOT}/install/setup.bash"
  echo "Start the monitor stack once first, or run: colcon build --symlink-install --packages-select uav_runtime_safety_monitor"
  exit 2
fi

source_setup "${REPO_ROOT}/install/setup.bash"

echo "Injecting synthetic monitor input: scenario=${SCENARIO}, duration=${DURATION_S}s"
echo "Expected monitor output appears in the monitor-stack terminal and data/px4_live_events.csv."
exec ros2 run uav_runtime_safety_monitor manual_violation_publisher \
  --ros-args \
  -p scenario:="${SCENARIO}" \
  -p duration_s:="${DURATION_S}" \
  -p publish_period_s:="${PUBLISH_PERIOD_S}"
