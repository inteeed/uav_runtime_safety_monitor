from typing import Optional


from uav_safety_core.mission_simulator import UAVState
from uav_safety_core.mission_supervisor import SupervisorDecision
from uav_safety_core.safety_monitor import SafetyResult

try:
    from uav_runtime_safety_monitor_msgs.msg import (
        SafetyStatus as SafetyStatusMsg,
    )
    from uav_runtime_safety_monitor_msgs.msg import (
        SupervisorResponse as SupervisorResponseMsg,
    )
    from uav_runtime_safety_monitor_msgs.msg import UAVState as UAVStateMsg

    _USING_GENERATED_MESSAGES = True
except ImportError:
    _USING_GENERATED_MESSAGES = False

    class UAVStateMsg:  # type: ignore
        def __init__(self) -> None:
            self.stamp = None
            self.time_s = 0.0
            self.frame_id = ""
            self.x_m = 0.0
            self.y_m = 0.0
            self.z_m = 0.0
            self.vx_mps = 0.0
            self.vy_mps = 0.0
            self.vz_mps = 0.0
            self.battery_percent = 0.0
            self.mission_state = ""
            self.has_planned_position = False
            self.planned_x_m = 0.0
            self.planned_y_m = 0.0
            self.planned_z_m = 0.0
            self.has_path_deviation = False
            self.path_deviation_m = 0.0

    class SafetyStatusMsg:  # type: ignore
        def __init__(self) -> None:
            self.stamp = None
            self.time_s = 0.0
            self.safety_status = ""
            self.severity = ""
            self.recommended_action = ""
            self.detail = ""

    class SupervisorResponseMsg:  # type: ignore
        def __init__(self) -> None:
            self.stamp = None
            self.time_s = 0.0
            self.supervisor_mode = ""
            self.active_response = ""
            self.response_reason = ""
            self.response_started = False


def typed_messages_available() -> bool:
    return _USING_GENERATED_MESSAGES


def ensure_typed_messages_available(logger=None) -> None:
    if typed_messages_available():
        return

    message = (
        "uav_runtime_safety_monitor_msgs is required for typed ROS2 topics. "
        "Build the workspace with colcon and source install/setup.bash."
    )
    if logger is not None:
        logger.error(message)
    raise ImportError(message)


def state_to_msg(state: UAVState, stamp=None) -> UAVStateMsg:
    message = UAVStateMsg()
    if stamp is not None:
        message.stamp = stamp
    message.time_s = float(state.time_s)
    message.frame_id = state.frame_id
    message.x_m = float(state.x_m)
    message.y_m = float(state.y_m)
    message.z_m = float(state.z_m)
    message.vx_mps = float(state.vx_mps)
    message.vy_mps = float(state.vy_mps)
    message.vz_mps = float(state.vz_mps)
    message.battery_percent = float(state.battery_percent)
    message.mission_state = state.mission_state

    has_planned = (
        state.planned_x_m is not None
        and state.planned_y_m is not None
        and state.planned_z_m is not None
    )
    message.has_planned_position = has_planned
    if has_planned:
        message.planned_x_m = float(state.planned_x_m)
        message.planned_y_m = float(state.planned_y_m)
        message.planned_z_m = float(state.planned_z_m)

    message.has_path_deviation = state.path_deviation_m is not None
    if state.path_deviation_m is not None:
        message.path_deviation_m = float(state.path_deviation_m)

    return message


def state_from_msg(message: UAVStateMsg) -> UAVState:
    planned_x_m: Optional[float] = None
    planned_y_m: Optional[float] = None
    planned_z_m: Optional[float] = None
    if getattr(message, "has_planned_position", False):
        planned_x_m = float(message.planned_x_m)
        planned_y_m = float(message.planned_y_m)
        planned_z_m = float(message.planned_z_m)

    path_deviation_m: Optional[float] = None
    if getattr(message, "has_path_deviation", False):
        path_deviation_m = float(message.path_deviation_m)

    return UAVState(
        time_s=float(message.time_s),
        x_m=float(message.x_m),
        y_m=float(message.y_m),
        z_m=float(message.z_m),
        vx_mps=float(message.vx_mps),
        vy_mps=float(message.vy_mps),
        vz_mps=float(message.vz_mps),
        battery_percent=float(message.battery_percent),
        mission_state=str(message.mission_state),
        frame_id=str(message.frame_id),
        planned_x_m=planned_x_m,
        planned_y_m=planned_y_m,
        planned_z_m=planned_z_m,
        path_deviation_m=path_deviation_m,
    )


def safety_result_to_msg(
    result: SafetyResult, time_s: float = 0.0, stamp=None
) -> SafetyStatusMsg:
    message = SafetyStatusMsg()
    if stamp is not None:
        message.stamp = stamp
    message.time_s = float(time_s)
    message.safety_status = result.safety_status
    message.severity = result.severity
    message.recommended_action = result.recommended_action
    message.detail = result.detail
    return message


def safety_result_from_msg(message: SafetyStatusMsg) -> SafetyResult:
    return SafetyResult(
        safety_status=str(message.safety_status),
        recommended_action=str(message.recommended_action),
        severity=str(message.severity),
        detail=str(message.detail),
    )


def supervisor_decision_to_msg(
    decision: SupervisorDecision, time_s: float = 0.0, stamp=None
) -> SupervisorResponseMsg:
    message = SupervisorResponseMsg()
    if stamp is not None:
        message.stamp = stamp
    message.time_s = float(time_s)
    message.supervisor_mode = decision.supervisor_mode
    message.active_response = decision.active_response
    message.response_reason = decision.response_reason
    message.response_started = bool(decision.response_started)
    return message


def supervisor_decision_from_msg(
    message: SupervisorResponseMsg,
) -> SupervisorDecision:
    return SupervisorDecision(
        supervisor_mode=str(message.supervisor_mode),
        active_response=str(message.active_response),
        response_reason=str(message.response_reason),
        response_started=bool(message.response_started),
    )
