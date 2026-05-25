from pathlib import Path

from mission_simulator import MissionSimulator
from safety_monitor import RuntimeSafetyMonitor, SafetyLimits
from scenario_catalog import SCENARIO_RUNS
from simulation_runner import SimulationRunResult, SimulationRunner


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "safety_limits.json"
DATA_DIR = PROJECT_ROOT / "data"

def print_scenario_summary(result: SimulationRunResult) -> None:
    print("{} mission written to {}".format(result.scenario.label, result.state_log_path))
    print("  event log: {}".format(result.event_log_path))
    print("  samples: {}".format(len(result.records)))
    print("  duration: {:.1f} s".format(result.duration_s))
    print("  events: {}".format(len(result.events)))
    if not result.non_safe_records:
        print("  result: SAFE")
        return

    report_state, report_result = result.selected_result()
    first_state, first_result = result.non_safe_records[0]
    print("  result: {}".format(report_result.safety_status))
    print("  severity: {}".format(report_result.severity))
    print("  first non-safe state at t={:.1f} s".format(first_state.time_s))
    if result.critical_records:
        print("  first critical state at t={:.1f} s".format(report_state.time_s))
    print("  action: {}".format(report_result.recommended_action))
    print("  detail: {}".format(report_result.detail))


def main() -> None:
    limits = SafetyLimits.from_json(CONFIG_PATH)
    simulator = MissionSimulator()
    monitor = RuntimeSafetyMonitor(limits)
    runner = SimulationRunner(simulator, monitor, DATA_DIR)

    for scenario in SCENARIO_RUNS:
        print_scenario_summary(runner.run(scenario))


if __name__ == "__main__":
    main()
