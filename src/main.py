from pathlib import Path
from typing import List, Tuple

from logger import write_mission_log
from mission_simulator import MissionSimulator, UAVState
from safety_monitor import RuntimeSafetyMonitor, SafetyLimits, SafetyResult


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "safety_limits.json"
DATA_DIR = PROJECT_ROOT / "data"


def run_scenario(
    scenario_name: str,
    output_path: Path,
    simulator: MissionSimulator,
    monitor: RuntimeSafetyMonitor,
) -> List[Tuple[UAVState, SafetyResult]]:
    states = simulator.generate(scenario_name)
    records = [(state, monitor.evaluate(state)) for state in states]
    write_mission_log(output_path, records)
    return records


def print_scenario_summary(
    label: str, output_path: Path, records: List[Tuple[UAVState, SafetyResult]]
) -> None:
    violations = [
        (state, result)
        for state, result in records
        if result.safety_status != "SAFE"
    ]

    print("{} mission written to {}".format(label, output_path))
    print("  samples: {}".format(len(records)))
    print("  duration: {:.1f} s".format(records[-1][0].time_s))
    if not violations:
        print("  result: SAFE")
        return

    first_state, first_result = violations[0]
    print("  result: {}".format(first_result.safety_status))
    print("  first violation at t={:.1f} s".format(first_state.time_s))
    print("  action: {}".format(first_result.recommended_action))
    print("  detail: {}".format(first_result.detail))


def main() -> None:
    limits = SafetyLimits.from_json(CONFIG_PATH)
    simulator = MissionSimulator()
    monitor = RuntimeSafetyMonitor(limits)

    scenarios = [
        ("Normal", "normal", DATA_DIR / "normal_mission.csv"),
        ("Unsafe geofence", "unsafe_geofence", DATA_DIR / "unsafe_mission.csv"),
    ]

    for label, scenario_name, output_path in scenarios:
        records = run_scenario(scenario_name, output_path, simulator, monitor)
        print_scenario_summary(label, output_path, records)


if __name__ == "__main__":
    main()

