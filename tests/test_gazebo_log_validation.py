import tempfile
import unittest
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "analysis"))

from validate_gazebo_logs import validate_log_dir


class GazeboLogValidationTest(unittest.TestCase):
    def test_valid_geofence_log_dir_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_dir = Path(tmp_dir)
            self._write_valid_geofence_logs(log_dir)

            failures = validate_log_dir(log_dir, "geofence_violation")

            self.assertEqual(failures, [])

    def test_missing_response_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_dir = Path(tmp_dir)
            self._write_valid_geofence_logs(log_dir)
            (log_dir / "mission_commander.log").write_text(
                "command WAYPOINT_2\n",
                encoding="utf-8",
            )

            failures = validate_log_dir(log_dir, "geofence_violation")

            self.assertTrue(
                any("Inserted supervisor response" in failure for failure in failures)
            )

    def test_plugin_error_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_dir = Path(tmp_dir)
            self._write_valid_geofence_logs(log_dir)
            (log_dir / "gzserver.log").write_text(
                "Failed to load plugin libgazebo_ros_state.so\n",
                encoding="utf-8",
            )

            failures = validate_log_dir(log_dir, "geofence_violation")

            self.assertIn("Gazebo ROS plugin loading error detected", failures)

    def test_gazebo_master_conflict_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_dir = Path(tmp_dir)
            self._write_valid_geofence_logs(log_dir)
            (log_dir / "gzserver.log").write_text(
                "\n".join(
                    [
                        "Gazebo multi-robot simulator, version 11.15.1",
                        "Unable to start server[bind: Address already in use]",
                    ]
                ),
                encoding="utf-8",
            )

            failures = validate_log_dir(log_dir, "geofence_violation")

            self.assertIn(
                "Gazebo server failed to start on its configured master URI",
                failures,
            )

    def _write_valid_geofence_logs(self, log_dir: Path) -> None:
        (log_dir / "gzserver.log").write_text(
            "Gazebo multi-robot simulator, version 11.15.1\n",
            encoding="utf-8",
        )
        (log_dir / "bridge.log").write_text(
            "Bridging Gazebo model 'safety_uav' from /model_states to /uav/state\n",
            encoding="utf-8",
        )
        (log_dir / "safety_monitor.log").write_text(
            "status=GEOFENCE_VIOLATION severity=CRITICAL action=RETURN_TO_HOME\n",
            encoding="utf-8",
        )
        (log_dir / "mission_supervisor.log").write_text(
            "supervisor_mode=RETURNING_HOME response=RETURN_TO_HOME\n",
            encoding="utf-8",
        )
        (log_dir / "mission_commander.log").write_text(
            "\n".join(
                [
                    "Inserted supervisor response 'RETURN_TO_HOME'",
                    "command RESPONSE_RETURN_HOME",
                    "command RESPONSE_LANDING",
                    "command RESPONSE_COMPLETE",
                ]
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
