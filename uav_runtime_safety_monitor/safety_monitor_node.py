from pathlib import Path

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from uav_runtime_safety_monitor.runtime_paths import runtime_file


from uav_safety_core.safety_monitor import RuntimeSafetyMonitor, SafetyLimits
from uav_runtime_safety_monitor.ros2_messages import (
    SafetyStatusMsg,
    UAVStateMsg,
    ensure_typed_messages_available,
    safety_result_to_msg,
    state_from_msg,
)


class SafetyMonitorNode(Node):
    """Subscribes to /uav/state and publishes safety-monitor decisions."""

    def __init__(self) -> None:
        super().__init__("safety_monitor_node")
        ensure_typed_messages_available(self.get_logger())
        default_limits_path = str(runtime_file("config", "safety_limits.json"))
        self.declare_parameter("safety_limits_path", default_limits_path)

        limits_path = Path(str(self.get_parameter("safety_limits_path").value))
        self._monitor = RuntimeSafetyMonitor(SafetyLimits.from_json(limits_path))
        self._previous_state = None
        self._last_logged_result_key = None
        self._status_publisher = self.create_publisher(
            SafetyStatusMsg, "/uav/safety_status", 10
        )
        self._action_publisher = self.create_publisher(
            String, "/uav/recommended_action", 10
        )
        self._subscription = self.create_subscription(
            UAVStateMsg, "/uav/state", self._on_state, 10
        )
        self.get_logger().info(
            "Safety monitor node ready with limits from {}".format(limits_path)
        )

    def _on_state(self, message: UAVStateMsg) -> None:
        state = state_from_msg(message)
        result = self._monitor.evaluate(
            state, previous_state=self._previous_state
        )
        self._previous_state = state

        status_message = safety_result_to_msg(
            result,
            time_s=state.time_s,
            stamp=self.get_clock().now().to_msg(),
        )
        self._status_publisher.publish(status_message)

        action_message = String()
        action_message.data = result.recommended_action
        self._action_publisher.publish(action_message)

        result_key = (
            result.safety_status,
            result.severity,
            result.recommended_action,
        )
        if result_key != self._last_logged_result_key:
            self._last_logged_result_key = result_key
            self.get_logger().info(
                "status={} severity={} action={}".format(
                    result.safety_status,
                    result.severity,
                    result.recommended_action,
                )
            )


def main() -> None:
    rclpy.init()
    node = SafetyMonitorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
