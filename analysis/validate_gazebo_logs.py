import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Dict, List


@dataclass(frozen=True)
class GazeboExpectation:
    scenario: str
    monitor_status: str
    recommended_action: str
    supervisor_mode: str
    commander_response: str
    response_command: str


EXPECTATIONS: Dict[str, GazeboExpectation] = {
    "geofence_violation": GazeboExpectation(
        scenario="geofence_violation",
        monitor_status="GEOFENCE_VIOLATION",
        recommended_action="RETURN_TO_HOME",
        supervisor_mode="RETURNING_HOME",
        commander_response="RETURN_TO_HOME",
        response_command="RESPONSE_RETURN_HOME",
    ),
    "unsafe_geofence": GazeboExpectation(
        scenario="unsafe_geofence",
        monitor_status="GEOFENCE_VIOLATION",
        recommended_action="RETURN_TO_HOME",
        supervisor_mode="RETURNING_HOME",
        commander_response="RETURN_TO_HOME",
        response_command="RESPONSE_RETURN_HOME",
    ),
    "altitude_violation": GazeboExpectation(
        scenario="altitude_violation",
        monitor_status="ALTITUDE_LIMIT_VIOLATION",
        recommended_action="LAND",
        supervisor_mode="LANDING",
        commander_response="LAND",
        response_command="RESPONSE_LANDING",
    ),
    "low_battery": GazeboExpectation(
        scenario="low_battery",
        monitor_status="LOW_BATTERY",
        recommended_action="LAND",
        supervisor_mode="LANDING",
        commander_response="LAND",
        response_command="RESPONSE_LANDING",
    ),
    "mission_timeout": GazeboExpectation(
        scenario="mission_timeout",
        monitor_status="MISSION_TIMEOUT",
        recommended_action="RETURN_TO_HOME",
        supervisor_mode="RETURNING_HOME",
        commander_response="RETURN_TO_HOME",
        response_command="RESPONSE_RETURN_HOME",
    ),
}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _gazebo_log_path(log_dir: Path) -> Path:
    headless_path = log_dir / "gzserver.log"
    if headless_path.exists():
        return headless_path
    return log_dir / "gazebo.log"


def _check_contains(
    label: str, text: str, expected: str, failures: List[str]
) -> None:
    if expected not in text:
        failures.append("{} missing '{}'".format(label, expected))


def validate_log_dir(log_dir: Path, scenario: str) -> List[str]:
    if scenario not in EXPECTATIONS:
        available = ", ".join(sorted(EXPECTATIONS))
        return [
            "Unknown scenario '{}'. Available scenarios: {}".format(
                scenario, available
            )
        ]

    expectation = EXPECTATIONS[scenario]
    failures: List[str] = []
    required_logs = {
        "Gazebo": _gazebo_log_path(log_dir),
        "Bridge": log_dir / "bridge.log",
        "Safety monitor": log_dir / "safety_monitor.log",
        "Mission supervisor": log_dir / "mission_supervisor.log",
        "Mission commander": log_dir / "mission_commander.log",
    }

    for label, path in required_logs.items():
        if not path.exists():
            failures.append("{} log does not exist: {}".format(label, path))

    gazebo_log = _read_text(required_logs["Gazebo"])
    bridge_log = _read_text(required_logs["Bridge"])
    monitor_log = _read_text(required_logs["Safety monitor"])
    supervisor_log = _read_text(required_logs["Mission supervisor"])
    commander_log = _read_text(required_logs["Mission commander"])

    if "Failed to load plugin" in gazebo_log or "incorrect plugin" in gazebo_log:
        failures.append("Gazebo ROS plugin loading error detected")

    if "Unable to start server" in gazebo_log or "Address already in use" in gazebo_log:
        failures.append("Gazebo server failed to start on its configured master URI")

    _check_contains("Gazebo log", gazebo_log, "Gazebo multi-robot simulator", failures)
    _check_contains("Bridge log", bridge_log, "Bridging Gazebo model", failures)
    _check_contains("Safety monitor log", monitor_log, expectation.monitor_status, failures)
    _check_contains("Safety monitor log", monitor_log, expectation.recommended_action, failures)
    _check_contains("Supervisor log", supervisor_log, expectation.supervisor_mode, failures)
    _check_contains("Supervisor log", supervisor_log, expectation.commander_response, failures)
    _check_contains(
        "Commander log",
        commander_log,
        "Inserted supervisor response '{}'".format(expectation.commander_response),
        failures,
    )
    _check_contains("Commander log", commander_log, expectation.response_command, failures)

    if expectation.response_command == "RESPONSE_RETURN_HOME":
        _check_contains("Commander log", commander_log, "RESPONSE_LANDING", failures)
    _check_contains("Commander log", commander_log, "RESPONSE_COMPLETE", failures)

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate logs from the Gazebo runtime safety demo."
    )
    parser.add_argument("log_dir", type=Path, help="Gazebo demo log directory")
    parser.add_argument(
        "--scenario",
        default="geofence_violation",
        help="Scenario expectation to validate",
    )
    args = parser.parse_args()

    failures = validate_log_dir(args.log_dir, args.scenario)
    if failures:
        print("Gazebo integration validation: FAIL")
        print("log_dir: {}".format(args.log_dir))
        for failure in failures:
            print("  - {}".format(failure))
        return 1

    expectation = EXPECTATIONS[args.scenario]
    print("Gazebo integration validation: PASS")
    print("log_dir: {}".format(args.log_dir))
    print("scenario: {}".format(expectation.scenario))
    print("monitor_status: {}".format(expectation.monitor_status))
    print("recommended_action: {}".format(expectation.recommended_action))
    print("supervisor_mode: {}".format(expectation.supervisor_mode))
    print("commander_response: {}".format(expectation.commander_response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
