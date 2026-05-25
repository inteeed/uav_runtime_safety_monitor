from dataclasses import dataclass
from typing import List

from scenario_catalog import MissionScenario, Waypoint


@dataclass(frozen=True)
class MissionSegment:
    target: Waypoint
    speed_mps: float
    mission_state: str


class MissionPhasePlanner:
    """Turns a scenario waypoint list into takeoff, cruise, return, and landing segments."""

    def build_segments(self, scenario: MissionScenario) -> List[MissionSegment]:
        segments = [
            MissionSegment(
                target=(0.0, 0.0, scenario.takeoff_altitude_m),
                speed_mps=scenario.climb_rate_mps,
                mission_state="TAKEOFF",
            )
        ]

        for index, waypoint in enumerate(scenario.waypoints, start=1):
            segments.append(
                MissionSegment(
                    target=waypoint,
                    speed_mps=scenario.cruise_speed_mps,
                    mission_state="WAYPOINT_{}".format(index),
                )
            )

        segments.extend(
            [
                MissionSegment(
                    target=(0.0, 0.0, scenario.takeoff_altitude_m),
                    speed_mps=scenario.cruise_speed_mps,
                    mission_state="RETURN_HOME",
                ),
                MissionSegment(
                    target=(0.0, 0.0, 0.0),
                    speed_mps=scenario.climb_rate_mps,
                    mission_state="LANDING",
                ),
            ]
        )
        return segments


class StateGapInjector:
    """Injects timestamp gaps to simulate missing state updates."""

    def apply(self, states, gap_after_s: float, gap_s: float):
        if gap_s <= 0.0:
            return states

        updated_states = []
        gap_inserted = False
        for state in states:
            if not gap_inserted and state.time_s > gap_after_s:
                gap_inserted = True

            time_offset = gap_s if gap_inserted else 0.0
            updated_states.append(
                state.__class__(
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

