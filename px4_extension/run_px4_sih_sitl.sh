#!/usr/bin/env bash
set -euo pipefail

PX4_AUTOPILOT_DIR="${PX4_AUTOPILOT_DIR:-${HOME}/projects/PX4-Autopilot}"
PX4_TOOLS_DIR="${PX4_TOOLS_DIR:-${HOME}/projects/px4_tools}"

if [[ ! -d "${PX4_AUTOPILOT_DIR}" ]]; then
  echo "PX4-Autopilot directory not found: ${PX4_AUTOPILOT_DIR}"
  echo "Set PX4_AUTOPILOT_DIR to the PX4 checkout."
  exit 2
fi

export PATH="${PX4_TOOLS_DIR}/bin:${HOME}/.local/bin:${PATH}"

cd "${PX4_AUTOPILOT_DIR}"
exec make px4_sitl sihsim_quadx
