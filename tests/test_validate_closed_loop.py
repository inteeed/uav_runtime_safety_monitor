import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "analysis"))

from validate_closed_loop import validate_command_log, validate_events


def _violation_event(frame_id: str) -> dict:
    return {
        "event_type": "ENTERED_VIOLATION",
        "frame_id": frame_id,
        "safety_status": "GEOFENCE_VIOLATION",
        "recommended_action": "RETURN_TO_HOME",
        "supervisor_mode": "RETURNING_HOME",
    }


class ValidateClosedLoopTest(unittest.TestCase):
    def test_real_flown_breach_passes(self) -> None:
        events = [_violation_event("px4_local_ned_converted")]
        self.assertEqual(
            validate_events(events, require_real_telemetry=True), []
        )

    def test_injected_breach_fails_real_telemetry_check(self) -> None:
        events = [_violation_event("px4_local_ned_fault_injected")]
        failures = validate_events(events, require_real_telemetry=True)
        self.assertTrue(any("injected telemetry" in f for f in failures))

    def test_injected_breach_still_passes_without_strict_flag(self) -> None:
        events = [_violation_event("px4_local_ned_fault_injected")]
        self.assertEqual(validate_events(events), [])

    def test_missing_violation_fails(self) -> None:
        events = [{"event_type": "CLEARED_EVENT", "safety_status": "SAFE"}]
        failures = validate_events(events)
        self.assertTrue(any("No ENTERED_VIOLATION" in f for f in failures))

    def test_missing_supervisor_response_fails(self) -> None:
        event = _violation_event("px4_local_ned_converted")
        event["supervisor_mode"] = "CONTINUE_MISSION"
        failures = validate_events([event])
        self.assertTrue(any("RETURNING_HOME" in f for f in failures))


class ValidateCommandLogTest(unittest.TestCase):
    def test_sent_rtl_command_passes(self) -> None:
        rows = [{"active_response": "RETURN_TO_HOME", "command": "20"}]
        self.assertEqual(validate_command_log(rows), [])

    def test_empty_command_log_fails(self) -> None:
        self.assertTrue(validate_command_log([]))

    def test_monitor_only_rows_fail(self) -> None:
        rows = [{"active_response": "MONITOR", "command": ""}]
        self.assertTrue(validate_command_log(rows))


if __name__ == "__main__":
    unittest.main()
