from pathlib import Path
import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
ROS2_DIR = PROJECT_ROOT / "ros2_extension"
for path in (SRC_DIR, ROS2_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from safety_monitor import RuntimeSafetyMonitor, SafetyLimits
from ros2_json import safety_result_to_json, state_from_json


CONFIG_PATH = PROJECT_ROOT / "config" / "safety_limits.json"


class SafetyMonitorNode(Node):
    """Subscribes to /uav/state and publishes safety-monitor decisions."""

    def __init__(self) -> None:
        super().__init__("safety_monitor_node")
        self._monitor = RuntimeSafetyMonitor(SafetyLimits.from_json(CONFIG_PATH))
        self._previous_state = None
        self._status_publisher = self.create_publisher(
            String, "/uav/safety_status", 10
        )
        self._action_publisher = self.create_publisher(
            String, "/uav/recommended_action", 10
        )
        self._subscription = self.create_subscription(
            String, "/uav/state", self._on_state, 10
        )
        self.get_logger().info("Safety monitor node ready")

    def _on_state(self, message: String) -> None:
        state = state_from_json(message.data)
        result = self._monitor.evaluate(
            state, previous_state=self._previous_state
        )
        self._previous_state = state

        status_message = String()
        status_message.data = safety_result_to_json(result)
        self._status_publisher.publish(status_message)

        action_message = String()
        action_message.data = result.recommended_action
        self._action_publisher.publish(action_message)

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

