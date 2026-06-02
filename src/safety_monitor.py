import json
from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Dict, List, Optional

from mission_simulator import UAVState


@dataclass(frozen=True)
class SafetyLimits:
    max_altitude_m: float
    altitude_warning_margin_m: float
    min_battery_percent: float
    max_mission_time_s: float
    max_state_update_gap_s: float
    max_velocity_mps: float
    path_deviation_warning_m: float
    path_deviation_violation_m: float
    geofence_warning_margin_m: float
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
            altitude_warning_margin_m=float(data["altitude_warning_margin_m"]),
            min_battery_percent=float(data["min_battery_percent"]),
            max_mission_time_s=float(data["max_mission_time_s"]),
            max_state_update_gap_s=float(data["max_state_update_gap_s"]),
            max_velocity_mps=float(data["max_velocity_mps"]),
            path_deviation_warning_m=float(data["path_deviation_warning_m"]),
            path_deviation_violation_m=float(data["path_deviation_violation_m"]),
            geofence_warning_margin_m=float(data["geofence_warning_margin_m"]),
            x_min_m=float(geofence["x_min_m"]),
            x_max_m=float(geofence["x_max_m"]),
            y_min_m=float(geofence["y_min_m"]),
            y_max_m=float(geofence["y_max_m"]),
        )


@dataclass(frozen=True)
class SafetyResult:
    safety_status: str
    recommended_action: str
    severity: str
    detail: str


@dataclass(frozen=True)
class _CandidateResult:
    result: SafetyResult
    priority: int


class RuntimeSafetyMonitor:
    """Checks UAV state samples against mission safety constraints."""

    def __init__(self, limits: SafetyLimits) -> None:
        self.limits = limits

    def evaluate(
        self, state: UAVState, previous_state: Optional[UAVState] = None
    ) -> SafetyResult:
        candidates: List[_CandidateResult] = []

        if previous_state is not None:
            update_gap_s = state.time_s - previous_state.time_s
            if update_gap_s > self.limits.max_state_update_gap_s:
                candidates.append(
                    _CandidateResult(
                        SafetyResult(
                            "STATE_TIMEOUT",
                            "RETURN_TO_HOME",
                            "CRITICAL",
                            "State update gap {:.1f} s exceeds {:.1f} s".format(
                                update_gap_s, self.limits.max_state_update_gap_s
                            ),
                        ),
                        95,
                    )
                )

        if state.z_m > self.limits.max_altitude_m:
            candidates.append(
                _CandidateResult(
                    SafetyResult(
                        "ALTITUDE_LIMIT_VIOLATION",
                        "LAND",
                        "CRITICAL",
                        "Altitude {:.1f} m exceeds {:.1f} m".format(
                            state.z_m, self.limits.max_altitude_m
                        ),
                    ),
                    100,
                )
            )

        if self._outside_geofence(state):
            candidates.append(
                _CandidateResult(
                    SafetyResult(
                        "GEOFENCE_VIOLATION",
                        "RETURN_TO_HOME",
                        "CRITICAL",
                        "Position ({:.1f}, {:.1f}) outside geofence".format(
                            state.x_m, state.y_m
                        ),
                    ),
                    90,
                )
            )

        speed_mps = self._speed(state)
        if speed_mps > self.limits.max_velocity_mps:
            candidates.append(
                _CandidateResult(
                    SafetyResult(
                        "VELOCITY_LIMIT_VIOLATION",
                        "RETURN_TO_HOME",
                        "CRITICAL",
                        "Velocity {:.1f} m/s exceeds {:.1f} m/s".format(
                            speed_mps, self.limits.max_velocity_mps
                        ),
                    ),
                    88,
                )
            )

        if state.battery_percent < self.limits.min_battery_percent:
            candidates.append(
                _CandidateResult(
                    SafetyResult(
                        "LOW_BATTERY",
                        "LAND",
                        "CRITICAL",
                        "Battery {:.1f}% below {:.1f}%".format(
                            state.battery_percent, self.limits.min_battery_percent
                        ),
                    ),
                    85,
                )
            )

        if state.time_s > self.limits.max_mission_time_s:
            candidates.append(
                _CandidateResult(
                    SafetyResult(
                        "MISSION_TIMEOUT",
                        "RETURN_TO_HOME",
                        "CRITICAL",
                        "Mission time {:.1f} s exceeds {:.1f} s".format(
                            state.time_s, self.limits.max_mission_time_s
                        ),
                    ),
                    80,
                )
            )

        if (
            state.path_deviation_m is not None
            and state.path_deviation_m > self.limits.path_deviation_violation_m
        ):
            candidates.append(
                _CandidateResult(
                    SafetyResult(
                        "PATH_DEVIATION_VIOLATION",
                        "RETURN_TO_HOME",
                        "CRITICAL",
                        "Path deviation {:.1f} m exceeds {:.1f} m".format(
                            state.path_deviation_m,
                            self.limits.path_deviation_violation_m,
                        ),
                    ),
                    70,
                )
            )

        altitude_warning_threshold = (
            self.limits.max_altitude_m - self.limits.altitude_warning_margin_m
        )
        if altitude_warning_threshold <= state.z_m <= self.limits.max_altitude_m:
            candidates.append(
                _CandidateResult(
                    SafetyResult(
                        "ALTITUDE_WARNING",
                        "WARNING",
                        "WARNING",
                        "Altitude {:.1f} m is within {:.1f} m of limit".format(
                            state.z_m, self.limits.altitude_warning_margin_m
                        ),
                    ),
                    45,
                )
            )

        if self._inside_geofence(state) and self._near_geofence_boundary(state):
            candidates.append(
                _CandidateResult(
                    SafetyResult(
                        "GEOFENCE_WARNING",
                        "WARNING",
                        "WARNING",
                        "Position ({:.1f}, {:.1f}) is within {:.1f} m of geofence".format(
                            state.x_m,
                            state.y_m,
                            self.limits.geofence_warning_margin_m,
                        ),
                    ),
                    40,
                )
            )

        if (
            state.path_deviation_m is not None
            and self.limits.path_deviation_warning_m
            <= state.path_deviation_m
            <= self.limits.path_deviation_violation_m
        ):
            candidates.append(
                _CandidateResult(
                    SafetyResult(
                        "PATH_DEVIATION_WARNING",
                        "WARNING",
                        "WARNING",
                        "Path deviation {:.1f} m is above {:.1f} m warning threshold".format(
                            state.path_deviation_m,
                            self.limits.path_deviation_warning_m,
                        ),
                    ),
                    35,
                )
            )

        if not candidates:
            return SafetyResult(
                "SAFE", "CONTINUE", "INFO", "All monitored constraints satisfied"
            )

        return max(candidates, key=lambda candidate: candidate.priority).result

    def _outside_geofence(self, state: UAVState) -> bool:
        return (
            state.x_m < self.limits.x_min_m
            or state.x_m > self.limits.x_max_m
            or state.y_m < self.limits.y_min_m
            or state.y_m > self.limits.y_max_m
        )

    def _inside_geofence(self, state: UAVState) -> bool:
        return not self._outside_geofence(state)

    def _near_geofence_boundary(self, state: UAVState) -> bool:
        distance_to_boundary_m = min(
            state.x_m - self.limits.x_min_m,
            self.limits.x_max_m - state.x_m,
            state.y_m - self.limits.y_min_m,
            self.limits.y_max_m - state.y_m,
        )
        return distance_to_boundary_m <= self.limits.geofence_warning_margin_m

    def _speed(self, state: UAVState) -> float:
        return sqrt(
            state.vx_mps * state.vx_mps
            + state.vy_mps * state.vy_mps
            + state.vz_mps * state.vz_mps
        )
