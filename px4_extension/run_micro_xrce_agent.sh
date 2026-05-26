#!/usr/bin/env bash
set -euo pipefail

AGENT_PREFIX="${MICRO_XRCE_AGENT_PREFIX:-${HOME}/projects/px4_tools/micro_xrce_agent}"
AGENT_BIN="${AGENT_PREFIX}/bin/MicroXRCEAgent"
AGENT_PORT="${PX4_UXRCE_PORT:-8888}"

if [[ ! -x "${AGENT_BIN}" ]]; then
  echo "MicroXRCEAgent not found: ${AGENT_BIN}"
  echo "Set MICRO_XRCE_AGENT_PREFIX to the install prefix that contains bin/MicroXRCEAgent."
  exit 2
fi

export LD_LIBRARY_PATH="${AGENT_PREFIX}/lib:${LD_LIBRARY_PATH:-}"

exec "${AGENT_BIN}" udp4 -p "${AGENT_PORT}"
