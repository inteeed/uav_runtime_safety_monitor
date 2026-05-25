import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mission_simulator import UAVState
from safety_monitor import RuntimeSafetyMonitor, SafetyLimits


def make_limits() -> SafetyLimits:
    return SafetyLimits(
        max_altitude_m=30.0,
        altitude_warning_margin_m=5.0,
        min_battery_percent=20.0,
        max_mission_time_s=120.0,
        max_state_update_gap_s=2.0,
        geofence_warning_margin_m=5.0,
        x_min_m=-50.0,
        x_max_m=50.0,
        y_min_m=-50.0,
        y_max_m=50.0,
    )


def make_state(
    time_s=10.0,
    x_m=0.0,
    y_m=0.0,
    z_m=20.0,
    battery_percent=80.0,
) -> UAVState:
    return UAVState(
        time_s=time_s,
        x_m=x_m,
        y_m=y_m,
        z_m=z_m,
        vx_mps=0.0,
        vy_mps=0.0,
        vz_mps=0.0,
        battery_percent=battery_percent,
        mission_state="TEST",
    )


class RuntimeSafetyMonitorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.monitor = RuntimeSafetyMonitor(make_limits())

    def test_safe_state(self) -> None:
        result = self.monitor.evaluate(make_state())
        self.assertEqual(result.safety_status, "SAFE")
        self.assertEqual(result.recommended_action, "CONTINUE")
        self.assertEqual(result.severity, "INFO")

    def test_geofence_warning(self) -> None:
        result = self.monitor.evaluate(make_state(x_m=46.0))
        self.assertEqual(result.safety_status, "GEOFENCE_WARNING")
        self.assertEqual(result.recommended_action, "WARNING")
        self.assertEqual(result.severity, "WARNING")

    def test_geofence_violation(self) -> None:
        result = self.monitor.evaluate(make_state(x_m=51.0))
        self.assertEqual(result.safety_status, "GEOFENCE_VIOLATION")
        self.assertEqual(result.recommended_action, "RETURN_TO_HOME")
        self.assertEqual(result.severity, "CRITICAL")

    def test_altitude_violation(self) -> None:
        result = self.monitor.evaluate(make_state(z_m=31.0))
        self.assertEqual(result.safety_status, "ALTITUDE_LIMIT_VIOLATION")
        self.assertEqual(result.recommended_action, "LAND")
        self.assertEqual(result.severity, "CRITICAL")

    def test_low_battery(self) -> None:
        result = self.monitor.evaluate(make_state(battery_percent=19.0))
        self.assertEqual(result.safety_status, "LOW_BATTERY")
        self.assertEqual(result.recommended_action, "LAND")
        self.assertEqual(result.severity, "CRITICAL")

    def test_mission_timeout(self) -> None:
        result = self.monitor.evaluate(make_state(time_s=121.0))
        self.assertEqual(result.safety_status, "MISSION_TIMEOUT")
        self.assertEqual(result.recommended_action, "RETURN_TO_HOME")
        self.assertEqual(result.severity, "CRITICAL")

    def test_state_timeout(self) -> None:
        previous_state = make_state(time_s=10.0)
        current_state = make_state(time_s=13.1)
        result = self.monitor.evaluate(current_state, previous_state=previous_state)
        self.assertEqual(result.safety_status, "STATE_TIMEOUT")
        self.assertEqual(result.recommended_action, "RETURN_TO_HOME")
        self.assertEqual(result.severity, "CRITICAL")

    def test_priority_prefers_altitude_violation_over_geofence_violation(self) -> None:
        result = self.monitor.evaluate(make_state(x_m=60.0, z_m=35.0))
        self.assertEqual(result.safety_status, "ALTITUDE_LIMIT_VIOLATION")
        self.assertEqual(result.recommended_action, "LAND")


if __name__ == "__main__":
    unittest.main()

