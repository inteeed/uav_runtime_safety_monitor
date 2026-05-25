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

from mission_simulator import UAVState
from mission_supervisor import MissionSupervisor
from ros2_json import (
    safety_result_from_json,
    supervisor_decision_to_json,
)


class MissionSupervisorNode(Node):
    """Consumes safety status and publishes a high-level supervisor mode."""

    def __init__(self) -> None:
        super().__init__("mission_supervisor_node")
        self._supervisor = MissionSupervisor()
        self._mode_publisher = self.create_publisher(
            String, "/uav/supervisor_mode", 10
        )
        self._subscription = self.create_subscription(
            String, "/uav/safety_status", self._on_safety_status, 10
        )
        self.get_logger().info("Mission supervisor node ready")

    def _on_safety_status(self, message: String) -> None:
        result = safety_result_from_json(message.data)
        synthetic_state = UAVState(
            time_s=0.0,
            x_m=0.0,
            y_m=0.0,
            z_m=0.0,
            vx_mps=0.0,
            vy_mps=0.0,
            vz_mps=0.0,
            battery_percent=100.0,
            mission_state="ROS2_STATUS_UPDATE",
        )
        decision = self._supervisor.update(synthetic_state, result)

        mode_message = String()
        mode_message.data = supervisor_decision_to_json(decision)
        self._mode_publisher.publish(mode_message)

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

