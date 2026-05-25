import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "ros2_extension"))

from mission_simulator import UAVState
from mission_supervisor import SupervisorDecision
from safety_monitor import SafetyResult
from ros2_json import (
    safety_result_from_json,
    safety_result_to_json,
    state_from_json,
    state_to_json,
    supervisor_decision_to_json,
)


class Ros2JsonTest(unittest.TestCase):
    def test_state_round_trip(self) -> None:
        state = UAVState(
            time_s=12.5,
            x_m=10.0,
            y_m=5.0,
            z_m=20.0,
            vx_mps=1.0,
            vy_mps=0.5,
            vz_mps=0.0,
            battery_percent=88.0,
            mission_state="WAYPOINT_1",
            frame_id="local_enu",
        )

        decoded = state_from_json(state_to_json(state))

        self.assertEqual(decoded.time_s, state.time_s)
        self.assertEqual(decoded.x_m, state.x_m)
        self.assertEqual(decoded.mission_state, state.mission_state)
        self.assertEqual(decoded.frame_id, state.frame_id)

    def test_safety_result_round_trip(self) -> None:
        result = SafetyResult(
            "GEOFENCE_VIOLATION",
            "RETURN_TO_HOME",
            "CRITICAL",
            "outside geofence",
        )

        decoded = safety_result_from_json(safety_result_to_json(result))

        self.assertEqual(decoded.safety_status, result.safety_status)
        self.assertEqual(decoded.recommended_action, result.recommended_action)
        self.assertEqual(decoded.severity, result.severity)

    def test_supervisor_decision_json(self) -> None:
        decision = SupervisorDecision(
            "RETURNING_HOME",
            "RETURN_TO_HOME",
            "GEOFENCE_VIOLATION",
            response_started=True,
        )

        payload = supervisor_decision_to_json(decision)

        self.assertIn("RETURNING_HOME", payload)
        self.assertIn("GEOFENCE_VIOLATION", payload)


if __name__ == "__main__":
    unittest.main()

