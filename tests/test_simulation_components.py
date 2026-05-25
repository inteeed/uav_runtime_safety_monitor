import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mission_simulator import MissionSimulator
from scenario_catalog import SCENARIOS, SCENARIO_RUNS
from simulation_components import MissionPhasePlanner, StateGapInjector


class SimulationComponentsTest(unittest.TestCase):
    def test_phase_planner_adds_takeoff_return_and_landing(self) -> None:
        scenario = SCENARIOS["normal"]
        segments = MissionPhasePlanner().build_segments(scenario)

        self.assertEqual(segments[0].mission_state, "TAKEOFF")
        self.assertEqual(segments[-2].mission_state, "RETURN_HOME")
        self.assertEqual(segments[-1].mission_state, "LANDING")
        self.assertEqual(len(segments), len(scenario.waypoints) + 3)

    def test_state_gap_injector_creates_expected_gap(self) -> None:
        states = MissionSimulator().generate("normal")
        injected_states = StateGapInjector().apply(states, gap_after_s=15.0, gap_s=4.0)
        gaps = [
            current.time_s - previous.time_s
            for previous, current in zip(injected_states, injected_states[1:])
        ]

        self.assertGreater(max(gaps), 4.0)

    def test_scenario_runs_have_expected_outcomes(self) -> None:
        scenario_names = {scenario.scenario_name for scenario in SCENARIO_RUNS}

        self.assertIn("normal", scenario_names)
        self.assertIn("geofence_violation", scenario_names)
        self.assertIn("state_timeout", scenario_names)
        for scenario in SCENARIO_RUNS:
            self.assertTrue(scenario.expected_status)
            self.assertTrue(scenario.expected_action)
            self.assertTrue(scenario.expected_severity)


if __name__ == "__main__":
    unittest.main()

