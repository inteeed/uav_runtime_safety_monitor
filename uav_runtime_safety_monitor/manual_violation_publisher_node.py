import json
import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ManualViolationPublisherNode(Node):
    """Publishes fault-injection commands for live monitor validation."""

    def __init__(self) -> None:
        super().__init__("manual_violation_publisher_node")
        self.declare_parameter("scenario", "geofence")
        self.declare_parameter("duration_s", 6.0)
        self.declare_parameter("publish_period_s", 0.05)
        self.declare_parameter("command_topic", "/uav/fault_injection")

        self._scenario = str(self.get_parameter("scenario").value)
        self._validate_scenario()
        self._duration_s = float(self.get_parameter("duration_s").value)
        self._command_topic = str(self.get_parameter("command_topic").value)
        publish_period_s = max(
            0.02, float(self.get_parameter("publish_period_s").value)
        )
        self._publisher = self.create_publisher(String, self._command_topic, 10)
        self._timer = self.create_timer(publish_period_s, self._publish_command)
        self._sample_count = 0
        self.done = False
        self.get_logger().info(
            "Requesting synthetic '{}' fault injection for {:.1f} s".format(
                self._scenario, self._duration_s
            )
        )

    def _validate_scenario(self) -> None:
        valid = {
            "geofence",
            "geofence_violation",
            "altitude",
            "altitude_violation",
            "battery",
            "low_battery",
        }
        if self._scenario.lower() not in valid:
            raise ValueError(
                "Unsupported scenario '{}'. Use geofence, altitude, or battery.".format(
                    self._scenario
                )
            )

    def _publish_command(self) -> None:
        if self._sample_count >= 10:
            self.get_logger().info(
                "Fault-injection request sent {} times".format(
                    self._sample_count
                )
            )
            self.done = True
            self._timer.cancel()
            return

        message = String()
        message.data = json.dumps(
            {
                "scenario": self._normalized_scenario(),
                "duration_s": self._duration_s,
            },
            sort_keys=True,
        )
        self._publisher.publish(message)
        self._sample_count += 1

    def _normalized_scenario(self) -> str:
        scenario = self._scenario.lower()
        if scenario in ("geofence", "geofence_violation"):
            return "geofence"

        if scenario in ("altitude", "altitude_violation"):
            return "altitude"

        if scenario in ("battery", "low_battery"):
            return "battery"

        raise AssertionError("Scenario validation failed unexpectedly.")


def main() -> int:
    rclpy.init()
    try:
        node = ManualViolationPublisherNode()
    except ValueError as error:
        print(error)
        rclpy.shutdown()
        return 2

    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
