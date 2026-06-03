import rclpy
import sys
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)

from uav_runtime_safety_monitor.px4_state_mapping import (
    battery_percent_from_px4_remaining,
    local_position_to_uav_state,
)


from uav_runtime_safety_monitor.ros2_messages import (
    UAVStateMsg,
    ensure_typed_messages_available,
    state_to_msg,
)


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
        ensure_typed_messages_available(self.get_logger())
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
        self.declare_parameter("publish_period_s", 0.1)

        local_position_topic = str(self.get_parameter("local_position_topic").value)
        battery_status_topic = str(self.get_parameter("battery_status_topic").value)
        publish_topic = str(self.get_parameter("publish_topic").value)
        self._battery_percent = float(
            self.get_parameter("fallback_battery_percent").value
        )
        self._mission_state = str(self.get_parameter("mission_state").value)
        self._publish_period_s = max(
            0.0, float(self.get_parameter("publish_period_s").value)
        )
        self._start_time = self.get_clock().now()
        self._last_publish_elapsed_s = None

        qos_profile = _px4_qos_profile()
        self._state_publisher = self.create_publisher(UAVStateMsg, publish_topic, 10)
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
            "PX4 bridge ready: {} + {} -> {} at up to {:.1f} Hz".format(
                local_position_topic,
                battery_status_topic,
                publish_topic,
                self._publish_rate_hz(),
            )
        )

    def _on_battery_status(self, message) -> None:
        self._battery_percent = battery_percent_from_px4_remaining(
            getattr(message, "remaining", None), self._battery_percent
        )

    def _on_local_position(self, message) -> None:
        now = self.get_clock().now()
        elapsed_s = (now - self._start_time).nanoseconds / 1e9
        if not self._should_publish(elapsed_s):
            return

        state = local_position_to_uav_state(
            message,
            time_s=elapsed_s,
            battery_percent=self._battery_percent,
            mission_state=self._mission_state,
        )

        output = state_to_msg(state, stamp=self.get_clock().now().to_msg())
        self._state_publisher.publish(output)

    def _should_publish(self, elapsed_s: float) -> bool:
        if self._last_publish_elapsed_s is None:
            self._last_publish_elapsed_s = elapsed_s
            return True

        if elapsed_s - self._last_publish_elapsed_s < self._publish_period_s:
            return False

        self._last_publish_elapsed_s = elapsed_s
        return True

    def _publish_rate_hz(self) -> float:
        if self._publish_period_s <= 0.0:
            return float("inf")
        return 1.0 / self._publish_period_s


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
