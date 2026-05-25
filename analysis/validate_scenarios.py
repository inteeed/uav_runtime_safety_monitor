import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mission_simulator import MissionSimulator
from safety_monitor import RuntimeSafetyMonitor, SafetyLimits
from scenario_catalog import SCENARIO_RUNS, ScenarioRun
from simulation_runner import SimulationRunResult, SimulationRunner


CONFIG_PATH = PROJECT_ROOT / "config" / "safety_limits.json"
DATA_DIR = PROJECT_ROOT / "data"


def expected_record(result: SimulationRunResult):
    if result.scenario.expected_status == "SAFE":
        return result.records[-1]
    if result.scenario.expected_severity == "CRITICAL":
        return result.critical_records[0] if result.critical_records else None
    return result.non_safe_records[0] if result.non_safe_records else None


def validate_result(result: SimulationRunResult) -> bool:
    selected = expected_record(result)
    if selected is None:
        return False

    _state, safety_result = selected
    scenario = result.scenario

    if scenario.expected_status == "SAFE":
        return not result.non_safe_records

    return (
        safety_result.safety_status == scenario.expected_status
        and safety_result.recommended_action == scenario.expected_action
        and safety_result.severity == scenario.expected_severity
    )


def print_validation_line(scenario: ScenarioRun, result: SimulationRunResult) -> bool:
    passed = validate_result(result)
    selected = expected_record(result)
    if selected is None:
        observed_status = "MISSING"
        observed_action = "MISSING"
        observed_severity = "MISSING"
    else:
        _state, safety_result = selected
        observed_status = safety_result.safety_status
        observed_action = safety_result.recommended_action
        observed_severity = safety_result.severity

    print(
        "{:<24} {:<5} expected={:<28} observed={:<28} action={:<14} severity={}".format(
            scenario.scenario_name,
            "PASS" if passed else "FAIL",
            scenario.expected_status,
            observed_status,
            observed_action,
            observed_severity,
        )
    )
    return passed


def main() -> None:
    limits = SafetyLimits.from_json(CONFIG_PATH)
    runner = SimulationRunner(
        MissionSimulator(), RuntimeSafetyMonitor(limits), DATA_DIR
    )

    print("Scenario validation")
    print("-" * 96)
    results = [runner.run(scenario) for scenario in SCENARIO_RUNS]
    passed = [
        print_validation_line(result.scenario, result) for result in results
    ]
    print("-" * 96)
    print("{} / {} scenarios passed".format(sum(passed), len(passed)))

    if not all(passed):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

