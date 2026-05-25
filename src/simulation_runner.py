from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from logger import SafetyEvent, extract_safety_events, write_event_log, write_mission_log
from mission_supervisor import MissionSupervisor, SupervisorDecision
from mission_simulator import MissionSimulator, UAVState
from safety_monitor import RuntimeSafetyMonitor, SafetyResult
from scenario_catalog import ScenarioRun


@dataclass(frozen=True)
class SimulationRunResult:
    scenario: ScenarioRun
    state_log_path: Path
    event_log_path: Path
    records: List[Tuple[UAVState, SafetyResult]]
    supervisor_decisions: List[SupervisorDecision]
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

    def selected_index(self) -> int:
        if self.critical_records:
            return self.records.index(self.critical_records[0])
        if self.non_safe_records:
            return self.records.index(self.non_safe_records[0])
        return len(self.records) - 1

    def selected_result(self) -> Tuple[UAVState, SafetyResult]:
        return self.records[self.selected_index()]

    def selected_decision(self) -> SupervisorDecision:
        return self.supervisor_decisions[self.selected_index()]


class SimulationRunner:
    """Runs one scenario through the simulator, monitor, and log writers."""

    def __init__(
        self,
        simulator: MissionSimulator,
        monitor: RuntimeSafetyMonitor,
        data_dir: Path,
        supervisor_factory=MissionSupervisor,
    ) -> None:
        self.simulator = simulator
        self.monitor = monitor
        self.data_dir = data_dir
        self.supervisor_factory = supervisor_factory

    def run(self, scenario: ScenarioRun) -> SimulationRunResult:
        state_log_path = self.data_dir / scenario.state_log_name
        event_log_path = self.data_dir / scenario.event_log_name
        states = self.simulator.generate(scenario.scenario_name)
        records: List[Tuple[UAVState, SafetyResult]] = []
        supervisor_decisions: List[SupervisorDecision] = []
        previous_state = None
        supervisor = self.supervisor_factory()

        for state in states:
            result = self.monitor.evaluate(state, previous_state=previous_state)
            decision = supervisor.update(state, result)
            records.append((state, result))
            supervisor_decisions.append(decision)
            previous_state = state

            if decision.response_started:
                for response_state in supervisor.generate_response_states(
                    state, decision
                ):
                    response_result = self.monitor.evaluate(
                        response_state, previous_state=previous_state
                    )
                    response_decision = supervisor.update(
                        response_state, response_result
                    )
                    records.append((response_state, response_result))
                    supervisor_decisions.append(response_decision)
                    previous_state = response_state
                break

        events = extract_safety_events(records, supervisor_decisions)
        write_mission_log(state_log_path, records, supervisor_decisions)
        write_event_log(event_log_path, events)

        return SimulationRunResult(
            scenario=scenario,
            state_log_path=state_log_path,
            event_log_path=event_log_path,
            records=records,
            supervisor_decisions=supervisor_decisions,
            events=events,
        )
