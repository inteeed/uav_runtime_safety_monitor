import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from uav_safety_core.mission_simulator import UAVState
from uav_safety_core.mission_supervisor import MissionSupervisor
from uav_safety_core.safety_monitor import SafetyResult


def make_state(
    time_s=10.0,
    x_m=20.0,
    y_m=0.0,
    z_m=20.0,
    mission_state="TEST",
) -> UAVState:
    return UAVState(
        time_s=time_s,
        x_m=x_m,
        y_m=y_m,
        z_m=z_m,
        vx_mps=0.0,
        vy_mps=0.0,
        vz_mps=0.0,
        battery_percent=80.0,
        mission_state=mission_state,
    )


class MissionSupervisorTest(unittest.TestCase):
    def test_warning_keeps_mission_active(self) -> None:
        supervisor = MissionSupervisor()
        decision = supervisor.update(
            make_state(),
            SafetyResult("GEOFENCE_WARNING", "WARNING", "WARNING", "near boundary"),
        )

        self.assertEqual(decision.supervisor_mode, "WARNING_ACTIVE")
        self.assertEqual(decision.active_response, "MONITOR")
        self.assertFalse(decision.response_started)

    def test_return_home_starts_response(self) -> None:
        supervisor = MissionSupervisor()
        decision = supervisor.update(
            make_state(x_m=60.0),
            SafetyResult(
                "GEOFENCE_VIOLATION",
                "RETURN_TO_HOME",
                "CRITICAL",
                "outside geofence",
            ),
        )

        self.assertEqual(decision.supervisor_mode, "RETURNING_HOME")
        self.assertEqual(decision.active_response, "RETURN_TO_HOME")
        self.assertTrue(decision.response_started)

        response_states = supervisor.generate_response_states(
            make_state(x_m=60.0), decision
        )
        self.assertEqual(response_states[-1].mission_state, "RESPONSE_COMPLETE")
        self.assertEqual(response_states[-1].x_m, 0.0)
        self.assertEqual(response_states[-1].y_m, 0.0)
        self.assertEqual(response_states[-1].z_m, 0.0)

    def test_land_starts_landing_response(self) -> None:
        supervisor = MissionSupervisor()
        state = make_state(x_m=15.0, y_m=10.0, z_m=35.0)
        decision = supervisor.update(
            state,
            SafetyResult(
                "ALTITUDE_LIMIT_VIOLATION", "LAND", "CRITICAL", "too high"
            ),
        )

        self.assertEqual(decision.supervisor_mode, "LANDING")
        self.assertEqual(decision.active_response, "LAND")
        self.assertTrue(decision.response_started)

        response_states = supervisor.generate_response_states(state, decision)
        self.assertEqual(response_states[-1].mission_state, "RESPONSE_COMPLETE")
        self.assertEqual(response_states[-1].x_m, 15.0)
        self.assertEqual(response_states[-1].y_m, 10.0)
        self.assertEqual(response_states[-1].z_m, 0.0)


if __name__ == "__main__":
    unittest.main()

