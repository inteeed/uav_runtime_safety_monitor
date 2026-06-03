import unittest

from uav_safety_core.mission_simulator import UAVState
from uav_safety_core.mission_supervisor import SupervisorDecision
from uav_safety_core.safety_monitor import SafetyResult
from uav_runtime_safety_monitor.ros2_messages import (
    safety_result_from_msg,
    safety_result_to_msg,
    state_from_msg,
    state_to_msg,
    supervisor_decision_from_msg,
    supervisor_decision_to_msg,
)


class Ros2MessagesTest(unittest.TestCase):
    def test_uav_state_round_trip_preserves_optional_reference_fields(self) -> None:
        state = UAVState(
            time_s=12.5,
            x_m=10.0,
            y_m=20.0,
            z_m=5.0,
            vx_mps=1.0,
            vy_mps=2.0,
            vz_mps=0.5,
            battery_percent=88.0,
            mission_state="WAYPOINT_2",
            frame_id="local_enu",
            planned_x_m=9.0,
            planned_y_m=19.0,
            planned_z_m=5.0,
            path_deviation_m=1.41,
        )

        decoded = state_from_msg(state_to_msg(state))

        self.assertEqual(decoded, state)

    def test_uav_state_round_trip_preserves_missing_optional_fields(self) -> None:
        state = UAVState(
            time_s=1.0,
            x_m=2.0,
            y_m=3.0,
            z_m=4.0,
            vx_mps=0.0,
            vy_mps=0.0,
            vz_mps=0.0,
            battery_percent=99.0,
            mission_state="PX4_TELEMETRY",
            frame_id="px4_local_ned_converted",
        )

        decoded = state_from_msg(state_to_msg(state))

        self.assertIsNone(decoded.planned_x_m)
        self.assertIsNone(decoded.planned_y_m)
        self.assertIsNone(decoded.planned_z_m)
        self.assertIsNone(decoded.path_deviation_m)
        self.assertEqual(decoded, state)

    def test_safety_status_round_trip(self) -> None:
        result = SafetyResult(
            "GEOFENCE_VIOLATION",
            "RETURN_TO_HOME",
            "CRITICAL",
            "Position outside geofence",
        )

        decoded = safety_result_from_msg(safety_result_to_msg(result, time_s=4.2))

        self.assertEqual(decoded, result)

    def test_supervisor_response_round_trip(self) -> None:
        decision = SupervisorDecision(
            supervisor_mode="RETURNING_HOME",
            active_response="RETURN_TO_HOME",
            response_reason="GEOFENCE_VIOLATION",
            response_started=True,
        )

        decoded = supervisor_decision_from_msg(
            supervisor_decision_to_msg(decision, time_s=4.2)
        )

        self.assertEqual(decoded, decision)


if __name__ == "__main__":
    unittest.main()
