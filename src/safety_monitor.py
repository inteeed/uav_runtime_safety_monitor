import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from mission_simulator import UAVState


@dataclass(frozen=True)
class SafetyLimits:
    max_altitude_m: float
    min_battery_percent: float
    max_mission_time_s: float
    x_min_m: float
    x_max_m: float
    y_min_m: float
    y_max_m: float

    @classmethod
    def from_json(cls, path: Path) -> "SafetyLimits":
        with path.open("r", encoding="utf-8") as handle:
            data: Dict[str, object] = json.load(handle)

        geofence = data["geofence"]
        return cls(
            max_altitude_m=float(data["max_altitude_m"]),
            min_battery_percent=float(data["min_battery_percent"]),
            max_mission_time_s=float(data["max_mission_time_s"]),
            x_min_m=float(geofence["x_min_m"]),
            x_max_m=float(geofence["x_max_m"]),
            y_min_m=float(geofence["y_min_m"]),
            y_max_m=float(geofence["y_max_m"]),
        )


@dataclass(frozen=True)
class SafetyResult:
    safety_status: str
    recommended_action: str
    detail: str


class RuntimeSafetyMonitor:
    """Checks UAV state samples against mission safety constraints."""

    def __init__(self, limits: SafetyLimits) -> None:
        self.limits = limits

    def evaluate(self, state: UAVState) -> SafetyResult:
        if state.z_m > self.limits.max_altitude_m:
            return SafetyResult(
                "ALTITUDE_LIMIT_VIOLATION",
                "LAND",
                "Altitude {:.1f} m exceeds {:.1f} m".format(
                    state.z_m, self.limits.max_altitude_m
                ),
            )

        if (
            state.x_m < self.limits.x_min_m
            or state.x_m > self.limits.x_max_m
            or state.y_m < self.limits.y_min_m
            or state.y_m > self.limits.y_max_m
        ):
            return SafetyResult(
                "GEOFENCE_VIOLATION",
                "RETURN_TO_HOME",
                "Position ({:.1f}, {:.1f}) outside geofence".format(
                    state.x_m, state.y_m
                ),
            )

        if state.battery_percent < self.limits.min_battery_percent:
            return SafetyResult(
                "LOW_BATTERY",
                "LAND",
                "Battery {:.1f}% below {:.1f}%".format(
                    state.battery_percent, self.limits.min_battery_percent
                ),
            )

        if state.time_s > self.limits.max_mission_time_s:
            return SafetyResult(
                "MISSION_TIMEOUT",
                "RETURN_TO_HOME",
                "Mission time {:.1f} s exceeds {:.1f} s".format(
                    state.time_s, self.limits.max_mission_time_s
                ),
            )

        return SafetyResult("SAFE", "CONTINUE", "All monitored constraints satisfied")

