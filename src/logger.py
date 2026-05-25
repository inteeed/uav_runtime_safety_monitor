import csv
from pathlib import Path
from typing import Iterable, Tuple

from mission_simulator import UAVState
from safety_monitor import SafetyResult


FIELDNAMES = [
    "time_s",
    "x_m",
    "y_m",
    "z_m",
    "vx_mps",
    "vy_mps",
    "vz_mps",
    "battery_percent",
    "mission_state",
    "safety_status",
    "recommended_action",
    "detail",
]


def write_mission_log(
    path: Path, records: Iterable[Tuple[UAVState, SafetyResult]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for state, result in records:
            writer.writerow(
                {
                    "time_s": state.time_s,
                    "x_m": state.x_m,
                    "y_m": state.y_m,
                    "z_m": state.z_m,
                    "vx_mps": state.vx_mps,
                    "vy_mps": state.vy_mps,
                    "vz_mps": state.vz_mps,
                    "battery_percent": state.battery_percent,
                    "mission_state": state.mission_state,
                    "safety_status": result.safety_status,
                    "recommended_action": result.recommended_action,
                    "detail": result.detail,
                }
            )

