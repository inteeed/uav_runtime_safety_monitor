"""Mapping from supervisor responses to PX4 MAVLink command IDs.

Kept ROS-free so the loop-closing logic can be unit tested without rclpy or
px4_msgs. See ``px4_command_bridge_node`` for the node that publishes them.
"""

import csv
from pathlib import Path
from typing import Optional, Union

from uav_safety_core.constants import ActiveResponse


# PX4 MAVLink command IDs (see px4_msgs/msg/VehicleCommand).
CMD_RETURN_TO_LAUNCH = 20  # VEHICLE_CMD_NAV_RETURN_TO_LAUNCH
CMD_LAND = 21  # VEHICLE_CMD_NAV_LAND

RESPONSE_TO_COMMAND = {
    ActiveResponse.RETURN_TO_HOME: CMD_RETURN_TO_LAUNCH,
    ActiveResponse.LAND: CMD_LAND,
}

COMMAND_LOG_FIELDNAMES = ["time_s", "active_response", "command"]


def command_for_response(active_response: str) -> Optional[int]:
    """Return the PX4 command ID for a supervisor response, or None.

    ``None`` means the response is not actionable as a vehicle command (for
    example a monitor-only warning), so no command should be sent.
    """
    return RESPONSE_TO_COMMAND.get(active_response)


def append_command_record(
    path: Union[str, Path],
    time_s: float,
    active_response: str,
    command: int,
) -> None:
    """Append one sent-command record to a CSV, writing a header if new.

    This is the machine-readable evidence that the command bridge actually
    issued a PX4 ``VehicleCommand`` (the validator checks it). Note it records
    that a command was *sent*, not that PX4 *accepted* it — that is confirmed
    separately from the resulting telemetry/trajectory.
    """
    path = Path(path)
    write_header = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COMMAND_LOG_FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "time_s": time_s,
                "active_response": active_response,
                "command": command,
            }
        )
