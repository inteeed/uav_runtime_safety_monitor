import rclpy
import sys
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)
from std_msgs.msg import String

from uav_runtime_safety_monitor.px4_state_mapping import (
    battery_percent_from_px4_remaining,
    local_position_to_uav_state,
)
from uav_runtime_safety_monitor.runtime_paths import add_runtime_paths


add_runtime_paths()

from ros2_json import state_to_json


def _px4_qos_profile() -> QoSProfile:
    return QoSProfile(
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.TRANSIENT_LOCAL,
        history=HistoryPolicy.KEEP_LAST,
        depth=10,
    )


class PX4StateBridgeNode(Node):
    """Converts PX4 ROS2 telemetry into the project's /uav/state topic."""

    def __init__(self) -> None:
        super().__init__("px4_state_bridge_node")
        try:
            from px4_msgs.msg import BatteryStatus, VehicleLocalPosition
        except ImportError as error:
            self.get_logger().error(
                "px4_msgs is required for PX4StateBridgeNode. "
                "Build/source a PX4 ROS2 workspace containing px4_msgs first."
            )
            raise error

        self.declare_parameter(
            "local_position_topic", "/fmu/out/vehicle_local_position"
        )
        self.declare_parameter("battery_status_topic", "/fmu/out/battery_status")
        self.declare_parameter("publish_topic", "/uav/state")
        self.declare_parameter("fallback_battery_percent", 100.0)
        self.declare_parameter("mission_state", "PX4_TELEMETRY")

        local_position_topic = str(self.get_parameter("local_position_topic").value)
        battery_status_topic = str(self.get_parameter("battery_status_topic").value)
        publish_topic = str(self.get_parameter("publish_topic").value)
        self._battery_percent = float(
            self.get_parameter("fallback_battery_percent").value
        )
        self._mission_state = str(self.get_parameter("mission_state").value)
        self._start_time = self.get_clock().now()

        qos_profile = _px4_qos_profile()
        self._state_publisher = self.create_publisher(String, publish_topic, 10)
        self._local_position_subscription = self.create_subscription(
            VehicleLocalPosition,
            local_position_topic,
            self._on_local_position,
            qos_profile,
        )
        self._battery_subscription = self.create_subscription(
            BatteryStatus,
            battery_status_topic,
            self._on_battery_status,
            qos_profile,
        )
        self.get_logger().info(
            "PX4 bridge ready: {} + {} -> {}".format(
                local_position_topic,
                battery_status_topic,
                publish_topic,
            )
        )

    def _on_battery_status(self, message) -> None:
        self._battery_percent = battery_percent_from_px4_remaining(
            getattr(message, "remaining", None), self._battery_percent
        )

    def _on_local_position(self, message) -> None:
        now = self.get_clock().now()
        elapsed_s = (now - self._start_time).nanoseconds / 1e9
        state = local_position_to_uav_state(
            message,
            time_s=elapsed_s,
            battery_percent=self._battery_percent,
            mission_state=self._mission_state,
        )

        output = String()
        output.data = state_to_json(state)
        self._state_publisher.publish(output)


def main() -> int:
    rclpy.init()
    try:
        node = PX4StateBridgeNode()
    except ImportError:
        rclpy.shutdown()
        return 2

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
