"""Validate that a PX4 live run actually closed the safety loop.

Reads a live event CSV (default ``data/px4_live_events.csv``) and checks the
*decision* chain:

  1. the monitor detected a geofence violation and recommended RETURN_TO_HOME,
  2. the supervisor responded (mode RETURNING_HOME),
  3. optionally, the violating sample came from *real* PX4 telemetry rather than
     the fault-injection node (``--require-real-telemetry``),
  4. optionally, the command bridge actually issued a PX4 command, by reading
     its command log (``--command-log data/px4_command_log.csv``).

Scope: this confirms the monitor/supervisor decision and (with --command-log)
that a VehicleCommand was *sent*. It does not by itself prove PX4 *accepted* the
command — confirm that from the resulting telemetry / trajectory plot.

The real-telemetry check separates a genuinely flown geofence breach (via
``trigger_real_geofence_flight.sh``) from a synthetic injected fault.
"""

import argparse
import csv
from pathlib import Path
import sys
from typing import Dict, List


GEOFENCE_VIOLATION = "GEOFENCE_VIOLATION"
RETURN_TO_HOME = "RETURN_TO_HOME"
RETURNING_HOME = "RETURNING_HOME"
ENTERED_VIOLATION = "ENTERED_VIOLATION"
INJECTED_MARKER = "fault_injected"
COMMAND_RESPONSES = ("RETURN_TO_HOME", "LAND")


def read_events(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_events(
    events: List[Dict[str, str]], require_real_telemetry: bool = False
) -> List[str]:
    failures: List[str] = []

    violations = [
        event
        for event in events
        if event.get("event_type") == ENTERED_VIOLATION
        and event.get("safety_status") == GEOFENCE_VIOLATION
    ]
    if not violations:
        failures.append("No ENTERED_VIOLATION event with GEOFENCE_VIOLATION found.")
        return failures

    violation = violations[0]

    if violation.get("recommended_action") != RETURN_TO_HOME:
        failures.append(
            "Geofence violation did not recommend {} (got {!r}).".format(
                RETURN_TO_HOME, violation.get("recommended_action")
            )
        )

    responded = any(
        event.get("supervisor_mode") == RETURNING_HOME for event in events
    )
    if not responded:
        failures.append(
            "Supervisor never entered {} in response to the violation.".format(
                RETURNING_HOME
            )
        )

    if require_real_telemetry:
        frame_id = violation.get("frame_id", "")
        if INJECTED_MARKER in frame_id:
            failures.append(
                "Violation came from injected telemetry (frame_id={!r}); "
                "expected a real flown breach.".format(frame_id)
            )

    return failures


def validate_command_log(rows: List[Dict[str, str]]) -> List[str]:
    """Check the command bridge actually issued an RTL/Land command."""
    sent = [
        row
        for row in rows
        if row.get("active_response") in COMMAND_RESPONSES
        and str(row.get("command", "")).strip() not in ("", "None")
    ]
    if not sent:
        return [
            "Command log has no RETURN_TO_HOME/LAND VehicleCommand record; "
            "the command bridge did not send a command."
        ]
    return []


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "events_csv",
        nargs="?",
        default="data/px4_live_events.csv",
        help="Live event CSV to validate.",
    )
    parser.add_argument(
        "--require-real-telemetry",
        action="store_true",
        help="Fail if the violation came from the fault-injection node.",
    )
    parser.add_argument(
        "--command-log",
        default=None,
        help=(
            "Command-bridge CSV (e.g. data/px4_command_log.csv). If given, "
            "require that an RTL/Land VehicleCommand was actually sent."
        ),
    )
    args = parser.parse_args(argv)

    path = Path(args.events_csv)
    if not path.exists():
        print("Event CSV not found: {}".format(path), file=sys.stderr)
        return 2

    failures = validate_events(
        read_events(path), require_real_telemetry=args.require_real_telemetry
    )

    command_log_checked = False
    if args.command_log is not None:
        command_log_path = Path(args.command_log)
        if not command_log_path.exists():
            failures.append(
                "Command log not found: {} (was the bridge enabled with "
                "command_log_path set?)".format(command_log_path)
            )
        else:
            command_log_checked = True
            failures.extend(validate_command_log(read_events(command_log_path)))

    print("Closed-loop validation: {}".format(path))
    if failures:
        for failure in failures:
            print("  FAIL  {}".format(failure))
        print("Result: FAIL")
        return 1

    print("  OK    geofence violation -> RETURN_TO_HOME -> supervisor RETURNING_HOME")
    if args.require_real_telemetry:
        print("  OK    violation came from real PX4 telemetry")
    if command_log_checked:
        print("  OK    command bridge sent an RTL/Land VehicleCommand")
    print("Result: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
