import csv
import tempfile
import unittest
from pathlib import Path

from uav_runtime_safety_monitor.live_log_writer import LiveLogWriter

from mission_simulator import UAVState
from mission_supervisor import SupervisorDecision, default_supervisor_decision
from safety_monitor import SafetyResult


class LiveLogWriterTest(unittest.TestCase):
    def test_writes_state_rows_and_event_transitions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            mission_log_path = root / "mission.csv"
            event_log_path = root / "events.csv"
            writer = LiveLogWriter(mission_log_path, event_log_path)
            writer.open()

            writer.record(
                UAVState(0.0, 0.0, 0.0, 3.0, 0.0, 0.0, 0.0, 100.0, "TEST"),
                SafetyResult(
                    "SAFE",
                    "CONTINUE",
                    "INFO",
                    "All monitored constraints satisfied",
                ),
                default_supervisor_decision(),
            )
            writer.record(
                UAVState(
                    1.0,
                    60.0,
                    0.0,
                    3.0,
                    0.0,
                    0.0,
                    0.0,
                    100.0,
                    "MANUAL_GEOFENCE_TEST",
                ),
                SafetyResult(
                    "GEOFENCE_VIOLATION",
                    "RETURN_TO_HOME",
                    "CRITICAL",
                    "Position (60.0, 0.0) outside geofence",
                ),
                SupervisorDecision(
                    "RETURNING_HOME",
                    "RETURN_TO_HOME",
                    "GEOFENCE_VIOLATION",
                    response_started=True,
                ),
            )
            writer.close()

            mission_rows = self._read_rows(mission_log_path)
            event_rows = self._read_rows(event_log_path)

            self.assertEqual(len(mission_rows), 2)
            self.assertEqual(mission_rows[1]["safety_status"], "GEOFENCE_VIOLATION")
            self.assertEqual(mission_rows[1]["supervisor_mode"], "RETURNING_HOME")
            self.assertEqual(len(event_rows), 1)
            self.assertEqual(event_rows[0]["event_type"], "ENTERED_VIOLATION")
            self.assertEqual(event_rows[0]["recommended_action"], "RETURN_TO_HOME")

    def _read_rows(self, path: Path):
        with path.open("r", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
