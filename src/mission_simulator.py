from dataclasses import dataclass
from math import ceil, sqrt
from typing import Iterable, List, Optional

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
    planned_x_m: Optional[float] = None
    planned_y_m: Optional[float] = None
    planned_z_m: Optional[float] = None
    path_deviation_m: Optional[float] = None


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
                planned_x_m=0.0,
                planned_y_m=0.0,
                planned_z_m=0.0,
                path_deviation_m=0.0,
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
                current.x_m,
                current.y_m,
                current.z_m,
                0.0,
            )
        )

        if mission.path_deviation_y_m != 0.0:
            states = self._inject_path_deviation(states, mission)

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
                    planned_x_m=round(start.x_m + ratio * dx, 2),
                    planned_y_m=round(start.y_m + ratio * dy, 2),
                    planned_z_m=round(start.z_m + ratio * dz, 2),
                    path_deviation_m=0.0,
                )
            )

        return segment_states

    def _inject_path_deviation(
        self, states: List[UAVState], mission
    ) -> List[UAVState]:
        updated_states: List[UAVState] = []
        for state in states:
            if not self._should_deviate(state, mission):
                updated_states.append(state)
                continue

            planned_x = state.planned_x_m if state.planned_x_m is not None else state.x_m
            planned_y = state.planned_y_m if state.planned_y_m is not None else state.y_m
            planned_z = state.planned_z_m if state.planned_z_m is not None else state.z_m
            x_m = state.x_m
            y_m = round(state.y_m + mission.path_deviation_y_m, 2)
            z_m = state.z_m
            deviation_m = sqrt(
                (x_m - planned_x) ** 2
                + (y_m - planned_y) ** 2
                + (z_m - planned_z) ** 2
            )
            updated_states.append(
                UAVState(
                    state.time_s,
                    x_m,
                    y_m,
                    z_m,
                    state.vx_mps,
                    state.vy_mps,
                    state.vz_mps,
                    state.battery_percent,
                    state.mission_state,
                    state.frame_id,
                    planned_x,
                    planned_y,
                    planned_z,
                    round(deviation_m, 2),
                )
            )

        return updated_states

    def _should_deviate(self, state: UAVState, mission) -> bool:
        if state.time_s < mission.path_deviation_start_s:
            return False
        if (
            mission.path_deviation_end_s > 0.0
            and state.time_s > mission.path_deviation_end_s
        ):
            return False
        return state.mission_state in mission.path_deviation_states
