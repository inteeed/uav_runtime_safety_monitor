from dataclasses import dataclass
from math import ceil, sqrt
from typing import Dict, Iterable, List, Tuple


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
    frame_id: str = "local_enu"


Waypoint = Tuple[float, float, float]


@dataclass(frozen=True)
class MissionScenario:
    waypoints: List[Waypoint]
    initial_battery_percent: float = 100.0
    takeoff_altitude_m: float = 20.0
    cruise_speed_mps: float = 5.0
    climb_rate_mps: float = 2.0
    time_gap_after_s: float = 0.0
    inserted_time_gap_s: float = 0.0


SCENARIOS: Dict[str, MissionScenario] = {
    "normal": MissionScenario(
        waypoints=[
            (15.0, 0.0, 20.0),
            (30.0, 20.0, 20.0),
            (5.0, 35.0, 18.0),
        ]
    ),
    "geofence_warning": MissionScenario(
        waypoints=[
            (20.0, 0.0, 20.0),
            (47.0, 8.0, 20.0),
            (10.0, 30.0, 18.0),
        ]
    ),
    "geofence_violation": MissionScenario(
        waypoints=[
            (20.0, 0.0, 20.0),
            (60.0, 10.0, 20.0),
            (5.0, 35.0, 18.0),
        ]
    ),
    "unsafe_geofence": MissionScenario(
        waypoints=[
            (20.0, 0.0, 20.0),
            (60.0, 10.0, 20.0),
            (5.0, 35.0, 18.0),
        ]
    ),
    "altitude_violation": MissionScenario(
        waypoints=[
            (15.0, 0.0, 20.0),
            (30.0, 20.0, 35.0),
            (5.0, 35.0, 18.0),
        ]
    ),
    "low_battery": MissionScenario(
        waypoints=[
            (15.0, 0.0, 20.0),
            (30.0, 20.0, 20.0),
            (5.0, 35.0, 18.0),
        ],
        initial_battery_percent=23.0,
    ),
    "mission_timeout": MissionScenario(
        waypoints=[
            (40.0, 0.0, 20.0),
            (40.0, 40.0, 20.0),
            (-40.0, 40.0, 20.0),
            (-40.0, -40.0, 20.0),
            (35.0, -35.0, 20.0),
        ],
        cruise_speed_mps=1.0,
    ),
    "state_timeout": MissionScenario(
        waypoints=[
            (15.0, 0.0, 20.0),
            (30.0, 20.0, 20.0),
            (5.0, 35.0, 18.0),
        ],
        time_gap_after_s=15.0,
        inserted_time_gap_s=4.0,
    ),
}


class MissionSimulator:
    """Generates simple waypoint-based UAV mission state data."""

    def __init__(
        self,
        dt_s: float = 1.0,
        battery_base_drain_percent_per_s: float = 0.055,
        battery_motion_drain_percent_per_s: float = 0.012,
    ) -> None:
        self.dt_s = dt_s
        self.battery_base_drain_percent_per_s = battery_base_drain_percent_per_s
        self.battery_motion_drain_percent_per_s = battery_motion_drain_percent_per_s

    def generate(self, scenario: str) -> List[UAVState]:
        """Return a list of UAV states for a named mission scenario."""
        if scenario not in SCENARIOS:
            available = ", ".join(sorted(SCENARIOS))
            raise ValueError(
                "Unknown scenario '{}'. Available scenarios: {}".format(
                    scenario, available
                )
            )

        mission = SCENARIOS[scenario]
        states: List[UAVState] = [
            UAVState(
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                mission.initial_battery_percent,
                "IDLE",
            )
        ]
        current = states[-1]

        states.extend(
            self._travel(
                current,
                target=(0.0, 0.0, mission.takeoff_altitude_m),
                speed_mps=mission.climb_rate_mps,
                mission_state="TAKEOFF",
            )
        )
        current = states[-1]

        for index, waypoint in enumerate(mission.waypoints, start=1):
            states.extend(
                self._travel(
                    current,
                    target=waypoint,
                    speed_mps=mission.cruise_speed_mps,
                    mission_state="WAYPOINT_{}".format(index),
                )
            )
            current = states[-1]

        states.extend(
            self._travel(
                current,
                target=(0.0, 0.0, mission.takeoff_altitude_m),
                speed_mps=mission.cruise_speed_mps,
                mission_state="RETURN_HOME",
            )
        )
        current = states[-1]

        states.extend(
            self._travel(
                current,
                target=(0.0, 0.0, 0.0),
                speed_mps=mission.climb_rate_mps,
                mission_state="LANDING",
            )
        )
        current = states[-1]

        states.append(
            UAVState(
                round(current.time_s + self.dt_s, 2),
                current.x_m,
                current.y_m,
                current.z_m,
                0.0,
                0.0,
                0.0,
                current.battery_percent,
                "MISSION_COMPLETE",
                current.frame_id,
            )
        )

        if mission.inserted_time_gap_s > 0.0:
            states = self._insert_time_gap(
                states, mission.time_gap_after_s, mission.inserted_time_gap_s
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
                    start.frame_id,
                )
            )

        return segment_states

    def _insert_time_gap(
        self, states: List[UAVState], gap_after_s: float, gap_s: float
    ) -> List[UAVState]:
        updated_states: List[UAVState] = []
        gap_inserted = False
        for state in states:
            if not gap_inserted and state.time_s > gap_after_s:
                gap_inserted = True
            time_offset = gap_s if gap_inserted else 0.0
            updated_states.append(
                UAVState(
                    round(state.time_s + time_offset, 2),
                    state.x_m,
                    state.y_m,
                    state.z_m,
                    state.vx_mps,
                    state.vy_mps,
                    state.vz_mps,
                    state.battery_percent,
                    state.mission_state,
                    state.frame_id,
                )
            )
        return updated_states

