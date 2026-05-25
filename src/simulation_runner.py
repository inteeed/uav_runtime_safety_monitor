from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from logger import SafetyEvent, extract_safety_events, write_event_log, write_mission_log
from mission_simulator import MissionSimulator, UAVState
from safety_monitor import RuntimeSafetyMonitor, SafetyResult
from scenario_catalog import ScenarioRun


@dataclass(frozen=True)
class SimulationRunResult:
    scenario: ScenarioRun
    state_log_path: Path
    event_log_path: Path
    records: List[Tuple[UAVState, SafetyResult]]
    events: List[SafetyEvent]

    @property
    def duration_s(self) -> float:
        return self.records[-1][0].time_s if self.records else 0.0

    @property
    def non_safe_records(self) -> List[Tuple[UAVState, SafetyResult]]:
        return [
            (state, result)
            for state, result in self.records
            if result.safety_status != "SAFE"
        ]

    @property
    def critical_records(self) -> List[Tuple[UAVState, SafetyResult]]:
        return [
            (state, result)
            for state, result in self.records
            if result.severity == "CRITICAL"
        ]

    def selected_result(self) -> Tuple[UAVState, SafetyResult]:
        if self.critical_records:
            return self.critical_records[0]
        if self.non_safe_records:
            return self.non_safe_records[0]
        return self.records[-1]


class SimulationRunner:
    """Runs one scenario through the simulator, monitor, and log writers."""

    def __init__(
        self,
        simulator: MissionSimulator,
        monitor: RuntimeSafetyMonitor,
        data_dir: Path,
    ) -> None:
        self.simulator = simulator
        self.monitor = monitor
        self.data_dir = data_dir

    def run(self, scenario: ScenarioRun) -> SimulationRunResult:
        state_log_path = self.data_dir / scenario.state_log_name
        event_log_path = self.data_dir / scenario.event_log_name
        states = self.simulator.generate(scenario.scenario_name)
        records: List[Tuple[UAVState, SafetyResult]] = []
        previous_state = None

        for state in states:
            result = self.monitor.evaluate(state, previous_state=previous_state)
            records.append((state, result))
            previous_state = state

        events = extract_safety_events(records)
        write_mission_log(state_log_path, records)
        write_event_log(event_log_path, events)

        return SimulationRunResult(
            scenario=scenario,
            state_log_path=state_log_path,
            event_log_path=event_log_path,
            records=records,
            events=events,
        )

