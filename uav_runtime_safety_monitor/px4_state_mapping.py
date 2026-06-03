from math import isfinite
from typing import Any


from uav_safety_core.mission_simulator import UAVState


def finite_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if not isfinite(result):
        return default
    return result


def battery_percent_from_px4_remaining(
    remaining: Any, fallback_percent: float
) -> float:
    remaining_value = finite_float(remaining, -1.0)
    if remaining_value < 0.0:
        return fallback_percent
    if remaining_value <= 1.0:
        return max(0.0, min(100.0, remaining_value * 100.0))
    return max(0.0, min(100.0, remaining_value))


def local_position_to_uav_state(
    position_message: Any,
    time_s: float,
    battery_percent: float,
    mission_state: str = "PX4_TELEMETRY",
) -> UAVState:
    """Convert PX4 NED local-position fields into the monitor state format.

    PX4 local position uses NED convention: x north, y east, z down.
    The safety monitor expects altitude as positive-up z, so z and vz are inverted.
    """

    return UAVState(
        time_s=round(float(time_s), 2),
        x_m=round(finite_float(getattr(position_message, "x", 0.0)), 2),
        y_m=round(finite_float(getattr(position_message, "y", 0.0)), 2),
        z_m=round(-finite_float(getattr(position_message, "z", 0.0)), 2),
        vx_mps=round(finite_float(getattr(position_message, "vx", 0.0)), 2),
        vy_mps=round(finite_float(getattr(position_message, "vy", 0.0)), 2),
        vz_mps=round(-finite_float(getattr(position_message, "vz", 0.0)), 2),
        battery_percent=round(float(battery_percent), 2),
        mission_state=mission_state,
        frame_id="px4_local_ned_converted",
    )
