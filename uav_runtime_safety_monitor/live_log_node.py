import json
from pathlib import Path

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from uav_runtime_safety_monitor.live_log_writer import LiveLogWriter
from uav_runtime_safety_monitor.runtime_paths import add_runtime_paths


add_runtime_paths()

from ros2_json import (
    safety_result_from_json,
    state_from_json,
    supervisor_decision_from_json,
)


class LiveLogNode(Node):
    """Records live ROS2 UAV state, safety status, and supervisor mode to CSV."""

    def __init__(self) -> None:
        super().__init__("live_log_node")
        self.declare_parameter("mission_log_path", "data/px4_live_mission.csv")
        self.declare_parameter("event_log_path", "data/px4_live_events.csv")

        mission_log_path = Path(
            str(self.get_parameter("mission_log_path").value)
        ).expanduser()
        event_log_path = Path(
            str(self.get_parameter("event_log_path").value)
        ).expanduser()
        self._writer = LiveLogWriter(mission_log_path, event_log_path)
        self._writer.open()
        self._latest_state = None
        self._latest_result = None
        self._last_record_key = None

        self.create_subscription(String, "/uav/state", self._on_state, 10)
        self.create_subscription(
            String, "/uav/safety_status", self._on_safety_status, 10
        )
        self.create_subscription(
            String, "/uav/supervisor_mode", self._on_supervisor_mode, 10
        )
        self.get_logger().info(
            "Live mission log: {}".format(mission_log_path.resolve())
        )
        self.get_logger().info(
            "Live event log: {}".format(event_log_path.resolve())
        )

    def _on_state(self, message: String) -> None:
        try:
            self._latest_state = state_from_json(message.data)
        except (json.JSONDecodeError, KeyError, ValueError) as error:
            self.get_logger().warn("Could not parse /uav/state: {}".format(error))

    def _on_safety_status(self, message: String) -> None:
        try:
            self._latest_result = safety_result_from_json(message.data)
        except (json.JSONDecodeError, KeyError, ValueError) as error:
            self.get_logger().warn(
                "Could not parse /uav/safety_status: {}".format(error)
            )

    def _on_supervisor_mode(self, message: String) -> None:
        if self._latest_state is None or self._latest_result is None:
            return

        try:
            decision = supervisor_decision_from_json(message.data)
        except (json.JSONDecodeError, KeyError, ValueError) as error:
            self.get_logger().warn(
                "Could not parse /uav/supervisor_mode: {}".format(error)
            )
            return

        record_key = (
            self._latest_state.time_s,
            self._latest_state.x_m,
            self._latest_state.y_m,
            self._latest_state.z_m,
            self._latest_result.safety_status,
            decision.supervisor_mode,
            decision.active_response,
        )
        if record_key == self._last_record_key:
            return

        self._writer.record(self._latest_state, self._latest_result, decision)
        self._last_record_key = record_key

    def destroy_node(self) -> bool:
        self.get_logger().info(
            "Live log closed: {} samples, {} event transitions".format(
                self._writer.sample_count,
                self._writer.event_count,
            )
        )
        self._writer.close()
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = LiveLogNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
