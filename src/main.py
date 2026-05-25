from pathlib import Path
from typing import List, Tuple

from logger import SafetyEvent, extract_safety_events, write_event_log, write_mission_log
from mission_simulator import MissionSimulator, UAVState
from safety_monitor import RuntimeSafetyMonitor, SafetyLimits, SafetyResult


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "safety_limits.json"
DATA_DIR = PROJECT_ROOT / "data"


SCENARIO_RUNS = [
    ("Normal", "normal", "normal_mission.csv"),
    ("Geofence warning", "geofence_warning", "geofence_warning_mission.csv"),
    ("Geofence violation", "geofence_violation", "geofence_violation_mission.csv"),
    ("Unsafe geofence alias", "unsafe_geofence", "unsafe_mission.csv"),
    ("Altitude violation", "altitude_violation", "altitude_violation_mission.csv"),
    ("Low battery", "low_battery", "low_battery_mission.csv"),
    ("Mission timeout", "mission_timeout", "timeout_mission.csv"),
    ("State timeout", "state_timeout", "state_timeout_mission.csv"),
]


def run_scenario(
    scenario_name: str,
    state_log_path: Path,
    event_log_path: Path,
    simulator: MissionSimulator,
    monitor: RuntimeSafetyMonitor,
) -> Tuple[List[Tuple[UAVState, SafetyResult]], List[SafetyEvent]]:
    states = simulator.generate(scenario_name)
    records: List[Tuple[UAVState, SafetyResult]] = []
    previous_state = None

    for state in states:
        result = monitor.evaluate(state, previous_state=previous_state)
        records.append((state, result))
        previous_state = state

    events = extract_safety_events(records)
    write_mission_log(state_log_path, records)
    write_event_log(event_log_path, events)
    return records, events


def print_scenario_summary(
    label: str,
    state_log_path: Path,
    event_log_path: Path,
    records: List[Tuple[UAVState, SafetyResult]],
    events: List[SafetyEvent],
) -> None:
    non_safe_records = [
        (state, result)
        for state, result in records
        if result.safety_status != "SAFE"
    ]
    critical_records = [
        (state, result)
        for state, result in records
        if result.severity == "CRITICAL"
    ]

    print("{} mission written to {}".format(label, state_log_path))
    print("  event log: {}".format(event_log_path))
    print("  samples: {}".format(len(records)))
    print("  duration: {:.1f} s".format(records[-1][0].time_s))
    print("  events: {}".format(len(events)))
    if not non_safe_records:
        print("  result: SAFE")
        return

    report_state, report_result = (
        critical_records[0] if critical_records else non_safe_records[0]
    )
    first_state, first_result = non_safe_records[0]
    print("  result: {}".format(report_result.safety_status))
    print("  severity: {}".format(report_result.severity))
    print("  first non-safe state at t={:.1f} s".format(first_state.time_s))
    if critical_records:
        print("  first critical state at t={:.1f} s".format(report_state.time_s))
    print("  action: {}".format(report_result.recommended_action))
    print("  detail: {}".format(report_result.detail))


def main() -> None:
    limits = SafetyLimits.from_json(CONFIG_PATH)
    simulator = MissionSimulator()
    monitor = RuntimeSafetyMonitor(limits)

    for label, scenario_name, state_log_name in SCENARIO_RUNS:
        state_log_path = DATA_DIR / state_log_name
        event_log_path = DATA_DIR / state_log_name.replace("_mission.csv", "_events.csv")
        records, events = run_scenario(
            scenario_name, state_log_path, event_log_path, simulator, monitor
        )
        print_scenario_summary(label, state_log_path, event_log_path, records, events)


if __name__ == "__main__":
    main()
