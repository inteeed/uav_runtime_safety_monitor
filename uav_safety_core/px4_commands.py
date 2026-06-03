"""Mapping from supervisor responses to PX4 MAVLink command IDs.

Kept ROS-free so the loop-closing logic can be unit tested without rclpy or
px4_msgs. See ``px4_command_bridge_node`` for the node that publishes them.
"""

from typing import Optional

from uav_safety_core.constants import ActiveResponse


# PX4 MAVLink command IDs (see px4_msgs/msg/VehicleCommand).
CMD_RETURN_TO_LAUNCH = 20  # VEHICLE_CMD_NAV_RETURN_TO_LAUNCH
CMD_LAND = 21  # VEHICLE_CMD_NAV_LAND

RESPONSE_TO_COMMAND = {
    ActiveResponse.RETURN_TO_HOME: CMD_RETURN_TO_LAUNCH,
    ActiveResponse.LAND: CMD_LAND,
}


def command_for_response(active_response: str) -> Optional[int]:
    """Return the PX4 command ID for a supervisor response, or None.

    ``None`` means the response is not actionable as a vehicle command (for
    example a monitor-only warning), so no command should be sent.
    """
    return RESPONSE_TO_COMMAND.get(active_response)
