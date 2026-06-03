import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from uav_safety_core.mission_simulator import UAVState
from uav_safety_core.safety_monitor import RuntimeSafetyMonitor, SafetyLimits


def make_limits() -> SafetyLimits:
    return SafetyLimits(
        max_altitude_m=30.0,
        altitude_warning_margin_m=5.0,
        min_battery_percent=20.0,
        max_mission_time_s=120.0,
        max_state_update_gap_s=2.0,
        max_velocity_mps=10.0,
        path_deviation_warning_m=5.0,
        path_deviation_violation_m=10.0,
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
    vx_mps=0.0,
    vy_mps=0.0,
    vz_mps=0.0,
    path_deviation_m=None,
) -> UAVState:
    return UAVState(
        time_s=time_s,
        x_m=x_m,
        y_m=y_m,
        z_m=z_m,
        vx_mps=vx_mps,
        vy_mps=vy_mps,
        vz_mps=vz_mps,
        battery_percent=battery_percent,
        mission_state="TEST",
        path_deviation_m=path_deviation_m,
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

    def test_velocity_limit_violation(self) -> None:
        result = self.monitor.evaluate(make_state(vx_mps=11.0))
        self.assertEqual(result.safety_status, "VELOCITY_LIMIT_VIOLATION")
        self.assertEqual(result.recommended_action, "RETURN_TO_HOME")
        self.assertEqual(result.severity, "CRITICAL")

    def test_path_deviation_warning(self) -> None:
        result = self.monitor.evaluate(make_state(path_deviation_m=6.0))
        self.assertEqual(result.safety_status, "PATH_DEVIATION_WARNING")
        self.assertEqual(result.recommended_action, "WARNING")
        self.assertEqual(result.severity, "WARNING")

    def test_path_deviation_violation(self) -> None:
        result = self.monitor.evaluate(make_state(path_deviation_m=12.0))
        self.assertEqual(result.safety_status, "PATH_DEVIATION_VIOLATION")
        self.assertEqual(result.recommended_action, "RETURN_TO_HOME")
        self.assertEqual(result.severity, "CRITICAL")

    def test_priority_prefers_altitude_violation_over_geofence_violation(self) -> None:
        result = self.monitor.evaluate(make_state(x_m=60.0, z_m=35.0))
        self.assertEqual(result.safety_status, "ALTITUDE_LIMIT_VIOLATION")
        self.assertEqual(result.recommended_action, "LAND")

    def test_computes_path_deviation_from_planned_position(self) -> None:
        # No pre-computed path_deviation_m: the monitor derives it from the
        # gap between the actual and planned position (12 m on the y axis).
        state = UAVState(
            time_s=10.0,
            x_m=0.0,
            y_m=12.0,
            z_m=20.0,
            vx_mps=0.0,
            vy_mps=0.0,
            vz_mps=0.0,
            battery_percent=80.0,
            mission_state="TEST",
            planned_x_m=0.0,
            planned_y_m=0.0,
            planned_z_m=20.0,
            path_deviation_m=None,
        )
        result = self.monitor.evaluate(state)
        self.assertEqual(result.safety_status, "PATH_DEVIATION_VIOLATION")
        self.assertEqual(result.recommended_action, "RETURN_TO_HOME")

    def test_planned_position_overrides_stale_supplied_deviation(self) -> None:
        # A state source claims zero deviation, but the planned vs actual gap
        # is 12 m; the monitor trusts its own computation, not the input.
        state = UAVState(
            time_s=10.0,
            x_m=0.0,
            y_m=12.0,
            z_m=20.0,
            vx_mps=0.0,
            vy_mps=0.0,
            vz_mps=0.0,
            battery_percent=80.0,
            mission_state="TEST",
            planned_x_m=0.0,
            planned_y_m=0.0,
            planned_z_m=20.0,
            path_deviation_m=0.0,
        )
        result = self.monitor.evaluate(state)
        self.assertEqual(result.safety_status, "PATH_DEVIATION_VIOLATION")


if __name__ == "__main__":
    unittest.main()
