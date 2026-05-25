from dataclasses import dataclass
from typing import Dict, List, Tuple


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


@dataclass(frozen=True)
class ScenarioRun:
    label: str
    scenario_name: str
    state_log_name: str
    expected_status: str
    expected_action: str
    expected_severity: str
    expected_supervisor_mode: str

    @property
    def event_log_name(self) -> str:
        return self.state_log_name.replace("_mission.csv", "_events.csv")


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


SCENARIO_RUNS = [
    ScenarioRun(
        "Normal",
        "normal",
        "normal_mission.csv",
        "SAFE",
        "CONTINUE",
        "INFO",
        "CONTINUE_MISSION",
    ),
    ScenarioRun(
        "Geofence warning",
        "geofence_warning",
        "geofence_warning_mission.csv",
        "GEOFENCE_WARNING",
        "WARNING",
        "WARNING",
        "WARNING_ACTIVE",
    ),
    ScenarioRun(
        "Geofence violation",
        "geofence_violation",
        "geofence_violation_mission.csv",
        "GEOFENCE_VIOLATION",
        "RETURN_TO_HOME",
        "CRITICAL",
        "RETURNING_HOME",
    ),
    ScenarioRun(
        "Unsafe geofence alias",
        "unsafe_geofence",
        "unsafe_mission.csv",
        "GEOFENCE_VIOLATION",
        "RETURN_TO_HOME",
        "CRITICAL",
        "RETURNING_HOME",
    ),
    ScenarioRun(
        "Altitude violation",
        "altitude_violation",
        "altitude_violation_mission.csv",
        "ALTITUDE_LIMIT_VIOLATION",
        "LAND",
        "CRITICAL",
        "LANDING",
    ),
    ScenarioRun(
        "Low battery",
        "low_battery",
        "low_battery_mission.csv",
        "LOW_BATTERY",
        "LAND",
        "CRITICAL",
        "LANDING",
    ),
    ScenarioRun(
        "Mission timeout",
        "mission_timeout",
        "timeout_mission.csv",
        "MISSION_TIMEOUT",
        "RETURN_TO_HOME",
        "CRITICAL",
        "RETURNING_HOME",
    ),
    ScenarioRun(
        "State timeout",
        "state_timeout",
        "state_timeout_mission.csv",
        "STATE_TIMEOUT",
        "RETURN_TO_HOME",
        "CRITICAL",
        "RETURNING_HOME",
    ),
]
