from dataclasses import dataclass
from math import ceil, sqrt
from typing import Iterable, List

from scenario_catalog import SCENARIOS
from simulation_components import MissionPhasePlanner, StateGapInjector

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


class MissionSimulator:
    """Generates simple waypoint-based UAV mission state data."""

    def __init__(
        self,
        dt_s: float = 1.0,
        battery_base_drain_percent_per_s: float = 0.055,
        battery_motion_drain_percent_per_s: float = 0.012,
        phase_planner: MissionPhasePlanner = None,
        state_gap_injector: StateGapInjector = None,
    ) -> None:
        self.dt_s = dt_s
        self.battery_base_drain_percent_per_s = battery_base_drain_percent_per_s
        self.battery_motion_drain_percent_per_s = battery_motion_drain_percent_per_s
        self.phase_planner = phase_planner or MissionPhasePlanner()
        self.state_gap_injector = state_gap_injector or StateGapInjector()

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

        for segment in self.phase_planner.build_segments(mission):
            states.extend(
                self._travel(
                    current,
                    target=segment.target,
                    speed_mps=segment.speed_mps,
                    mission_state=segment.mission_state,
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
            states = self.state_gap_injector.apply(
                states, mission.time_gap_after_s, mission.inserted_time_gap_s
            )

        return states

    def _travel(
        self,
        start: UAVState,
        target,
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
