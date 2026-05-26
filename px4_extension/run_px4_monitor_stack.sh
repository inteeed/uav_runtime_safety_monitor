#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROS_SETUP="${ROS_SETUP:-/opt/ros/foxy/setup.bash}"
PX4_ROS2_WS_SETUP="${PX4_ROS2_WS_SETUP:-}"

if env | grep -E '^(ROS_PACKAGE_PATH|CMAKE_PREFIX_PATH|PYTHONPATH|LD_LIBRARY_PATH|PATH)=' | grep -q '/noetic'; then
  echo "Current shell contains ROS Noetic paths. Open a clean terminal before running PX4/ROS2."
  exit 2
fi

if [[ "${ROS_DISTRO:-}" == "noetic" ]]; then
  echo "ROS_DISTRO is set to noetic. Open a clean terminal before running PX4/ROS2."
  exit 2
fi

if [[ ! -f "${ROS_SETUP}" ]]; then
  echo "ROS setup file not found: ${ROS_SETUP}"
  exit 2
fi

source "${ROS_SETUP}"

if [[ -n "${PX4_ROS2_WS_SETUP}" ]]; then
  if [[ ! -f "${PX4_ROS2_WS_SETUP}" ]]; then
    echo "PX4_ROS2_WS_SETUP does not exist: ${PX4_ROS2_WS_SETUP}"
    exit 2
  fi
  source "${PX4_ROS2_WS_SETUP}"
fi

cd "${REPO_ROOT}"

CHECK_ARGS=(--strict)
if [[ -n "${PX4_ROS2_WS_SETUP}" ]]; then
  CHECK_ARGS+=(--extra-setup "${PX4_ROS2_WS_SETUP}")
fi

python3 px4_extension/check_px4_environment.py "${CHECK_ARGS[@]}"

colcon build --symlink-install --packages-select uav_runtime_safety_monitor
source install/setup.bash

ros2 launch uav_runtime_safety_monitor px4_safety_monitor.launch.py
