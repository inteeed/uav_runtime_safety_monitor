from dataclasses import dataclass
from math import ceil, sqrt
from typing import Iterable, List, Tuple


@dataclass(frozen=True)
class UAVState:
    time_s: float
    x_m: float
    y_m: float
    z_m: float
    vx_mps: float
    vy_mps: float
    vz_mps: float
    battery_percent: float
    mission_state: str


Waypoint = Tuple[float, float, float]


class MissionSimulator:
    """Generates simple waypoint-based UAV mission state data."""

    def __init__(
        self,
        dt_s: float = 1.0,
        cruise_speed_mps: float = 5.0,
        climb_rate_mps: float = 2.0,
        battery_base_drain_percent_per_s: float = 0.055,
        battery_motion_drain_percent_per_s: float = 0.012,
    ) -> None:
        self.dt_s = dt_s
        self.cruise_speed_mps = cruise_speed_mps
        self.climb_rate_mps = climb_rate_mps
        self.battery_base_drain_percent_per_s = battery_base_drain_percent_per_s
        self.battery_motion_drain_percent_per_s = battery_motion_drain_percent_per_s

    def generate(self, scenario: str) -> List[UAVState]:
        """Return a list of UAV states for a named mission scenario."""
        if scenario == "normal":
            waypoints = [
                (15.0, 0.0, 20.0),
                (30.0, 20.0, 20.0),
                (5.0, 35.0, 18.0),
            ]
        elif scenario == "unsafe_geofence":
            waypoints = [
                (20.0, 0.0, 20.0),
                (60.0, 10.0, 20.0),
                (5.0, 35.0, 18.0),
            ]
        else:
            raise ValueError(
                "Unknown scenario '{}'. Use 'normal' or 'unsafe_geofence'.".format(
                    scenario
                )
            )

        states: List[UAVState] = [
            UAVState(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 100.0, "IDLE")
        ]
        current = states[-1]

        states.extend(
            self._travel(
                current,
                target=(0.0, 0.0, 20.0),
                speed_mps=self.climb_rate_mps,
                mission_state="TAKEOFF",
            )
        )
        current = states[-1]

        for index, waypoint in enumerate(waypoints, start=1):
            states.extend(
                self._travel(
                    current,
                    target=waypoint,
                    speed_mps=self.cruise_speed_mps,
                    mission_state="WAYPOINT_{}".format(index),
                )
            )
            current = states[-1]

        states.extend(
            self._travel(
                current,
                target=(0.0, 0.0, 20.0),
                speed_mps=self.cruise_speed_mps,
                mission_state="RETURN_HOME",
            )
        )
        current = states[-1]

        states.extend(
            self._travel(
                current,
                target=(0.0, 0.0, 0.0),
                speed_mps=self.climb_rate_mps,
                mission_state="LANDING",
            )
        )
        current = states[-1]

        states.append(
            UAVState(
                current.time_s + self.dt_s,
                current.x_m,
                current.y_m,
                current.z_m,
                0.0,
                0.0,
                0.0,
                current.battery_percent,
                "MISSION_COMPLETE",
            )
        )
        return states

    def _travel(
        self,
        start: UAVState,
        target: Waypoint,
        speed_mps: float,
        mission_state: str,
    ) -> Iterable[UAVState]:
        dx = target[0] - start.x_m
        dy = target[1] - start.y_m
        dz = target[2] - start.z_m
        distance_m = sqrt(dx * dx + dy * dy + dz * dz)
        if distance_m == 0.0:
            return []

        duration_s = distance_m / speed_mps
        steps = max(1, int(ceil(duration_s / self.dt_s)))
        step_duration_s = duration_s / steps

        vx = dx / duration_s
        vy = dy / duration_s
        vz = dz / duration_s
        speed = sqrt(vx * vx + vy * vy + vz * vz)

        segment_states: List[UAVState] = []
        battery = start.battery_percent
        for step in range(1, steps + 1):
            ratio = float(step) / float(steps)
            time_s = start.time_s + step * step_duration_s
            battery -= (
                self.battery_base_drain_percent_per_s
                + self.battery_motion_drain_percent_per_s * speed
            ) * step_duration_s
            segment_states.append(
                UAVState(
                    round(time_s, 2),
                    round(start.x_m + ratio * dx, 2),
                    round(start.y_m + ratio * dy, 2),
                    round(start.z_m + ratio * dz, 2),
                    round(vx, 2),
                    round(vy, 2),
                    round(vz, 2),
                    round(max(0.0, battery), 2),
                    mission_state,
                )
            )

        return segment_states

