import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from uav_runtime_safety_monitor.runtime_paths import add_runtime_paths


add_runtime_paths()

from mission_simulator import MissionSimulator
from ros2_json import state_to_json


class UAVStatePublisherNode(Node):
    """Publishes simulated UAV state samples as JSON on /uav/state."""

    def __init__(self) -> None:
        super().__init__("uav_state_publisher_node")
        self.declare_parameter("scenario", "geofence_violation")
        self.declare_parameter("publish_period_s", 0.5)

        scenario = str(self.get_parameter("scenario").value)
        publish_period_s = float(self.get_parameter("publish_period_s").value)

        self._publisher = self.create_publisher(String, "/uav/state", 10)
        self._states = MissionSimulator().generate(scenario)
        self._index = 0
        self._timer = self.create_timer(publish_period_s, self._publish_next_state)
        self.get_logger().info(
            "Publishing scenario '{}' with {} samples".format(
                scenario, len(self._states)
            )
        )

    def _publish_next_state(self) -> None:
        if self._index >= len(self._states):
            self.get_logger().info("Scenario complete")
            self._timer.cancel()
            return

        state = self._states[self._index]
        message = String()
        message.data = state_to_json(state)
        self._publisher.publish(message)
        self.get_logger().info(
            "state t={:.1f}s {} x={:.1f} y={:.1f} z={:.1f}".format(
                state.time_s,
                state.mission_state,
                state.x_m,
                state.y_m,
                state.z_m,
            )
        )
        self._index += 1


def main() -> None:
    rclpy.init()
    node = UAVStatePublisherNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
