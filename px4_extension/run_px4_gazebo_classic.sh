#!/usr/bin/env bash
set -euo pipefail

PX4_AUTOPILOT_DIR="${PX4_AUTOPILOT_DIR:-${HOME}/projects/PX4-Autopilot}"
PX4_TOOLS_DIR="${PX4_TOOLS_DIR:-${HOME}/projects/px4_tools}"
HEADLESS_MODE="${HEADLESS:-1}"

if [[ ! -d "${PX4_AUTOPILOT_DIR}" ]]; then
  echo "PX4-Autopilot directory not found: ${PX4_AUTOPILOT_DIR}"
  echo "Set PX4_AUTOPILOT_DIR to the PX4 checkout."
  exit 2
fi

export PATH="${PX4_TOOLS_DIR}/bin:${HOME}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
unset ROS_DISTRO ROS_PACKAGE_PATH CMAKE_PREFIX_PATH PYTHONPATH LD_LIBRARY_PATH MAKE

cd "${PX4_AUTOPILOT_DIR}"
if [[ "${HEADLESS_MODE}" == "0" || "${HEADLESS_MODE,,}" == "false" || "${HEADLESS_MODE,,}" == "no" ]]; then
  exec env -u HEADLESS make px4_sitl gazebo-classic
fi

exec env HEADLESS=1 make px4_sitl gazebo-classic
