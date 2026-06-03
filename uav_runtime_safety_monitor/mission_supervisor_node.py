import rclpy
from rclpy.node import Node


from dataclasses import replace

from uav_safety_core.mission_simulator import UAVState
from uav_safety_core.mission_supervisor import MissionSupervisor
from uav_runtime_safety_monitor.ros2_messages import (
    SafetyStatusMsg,
    SupervisorResponseMsg,
    UAVStateMsg,
    ensure_typed_messages_available,
    safety_result_from_msg,
    state_from_msg,
    supervisor_decision_to_msg,
)


class MissionSupervisorNode(Node):
    """Consumes safety status and publishes a high-level supervisor mode."""

    def __init__(self) -> None:
        super().__init__("mission_supervisor_node")
        ensure_typed_messages_available(self.get_logger())
        self._supervisor = MissionSupervisor()
        self._last_logged_decision_key = None
        self._latest_state = None
        self._mode_publisher = self.create_publisher(
            SupervisorResponseMsg, "/uav/supervisor_mode", 10
        )
        # Cache the live vehicle state so supervisor decisions and any response
        # trajectory are based on the real pose rather than a zeroed placeholder.
        self._state_subscription = self.create_subscription(
            UAVStateMsg, "/uav/state", self._on_state, 10
        )
        self._subscription = self.create_subscription(
            SafetyStatusMsg, "/uav/safety_status", self._on_safety_status, 10
        )
        self.get_logger().info("Mission supervisor node ready")

    def _on_state(self, message: UAVStateMsg) -> None:
        self._latest_state = state_from_msg(message)

    def _current_state(self, status_time_s: float) -> UAVState:
        if self._latest_state is not None:
            return replace(self._latest_state, time_s=status_time_s)
        # No telemetry seen yet: fall back to a neutral placeholder so the
        # supervisor can still react to the safety status.
        return UAVState(
            time_s=status_time_s,
            x_m=0.0,
            y_m=0.0,
            z_m=0.0,
            vx_mps=0.0,
            vy_mps=0.0,
            vz_mps=0.0,
            battery_percent=100.0,
            mission_state="ROS2_STATUS_UPDATE",
        )

    def _on_safety_status(self, message: SafetyStatusMsg) -> None:
        result = safety_result_from_msg(message)
        state = self._current_state(float(message.time_s))
        decision = self._supervisor.update(state, result)

        mode_message = supervisor_decision_to_msg(
            decision,
            time_s=float(message.time_s),
            stamp=self.get_clock().now().to_msg(),
        )
        self._mode_publisher.publish(mode_message)

        decision_key = (
            decision.supervisor_mode,
            decision.active_response,
            decision.response_reason,
        )
        if decision_key != self._last_logged_decision_key:
            self._last_logged_decision_key = decision_key
            self.get_logger().info(
                "supervisor_mode={} response={} reason={}".format(
                    decision.supervisor_mode,
                    decision.active_response,
                    decision.response_reason,
                )
            )


def main() -> None:
    rclpy.init()
    node = MissionSupervisorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
