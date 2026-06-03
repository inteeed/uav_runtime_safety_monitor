from math import sqrt

import rclpy
from rclpy.node import Node
from gazebo_msgs.msg import ModelStates


from uav_safety_core.mission_simulator import UAVState
from uav_runtime_safety_monitor.ros2_messages import (
    UAVStateMsg,
    ensure_typed_messages_available,
    state_to_msg,
)


class GazeboStateBridgeNode(Node):
    """Bridges Gazebo model state into the project's /uav/state topic."""

    def __init__(self) -> None:
        super().__init__("gazebo_state_bridge_node")
        ensure_typed_messages_available(self.get_logger())
        self.declare_parameter("model_name", "safety_uav")
        self.declare_parameter("battery_start_percent", 100.0)
        self.declare_parameter("battery_base_drain_percent_per_s", 0.055)
        self.declare_parameter("battery_motion_drain_percent_per_s", 0.012)

        self._model_name = str(self.get_parameter("model_name").value)
        self._battery_percent = float(
            self.get_parameter("battery_start_percent").value
        )
        self._battery_base_drain = float(
            self.get_parameter("battery_base_drain_percent_per_s").value
        )
        self._battery_motion_drain = float(
            self.get_parameter("battery_motion_drain_percent_per_s").value
        )
        self._start_time = self.get_clock().now()
        self._previous_time = None

        self._publisher = self.create_publisher(UAVStateMsg, "/uav/state", 10)
        self._subscription = self.create_subscription(
            ModelStates, "/model_states", self._on_model_states, 10
        )
        self.get_logger().info(
            "Bridging Gazebo model '{}' from /model_states to /uav/state".format(
                self._model_name
            )
        )

    def _on_model_states(self, message: ModelStates) -> None:
        if self._model_name not in message.name:
            return

        index = message.name.index(self._model_name)
        pose = message.pose[index]
        twist = message.twist[index]
        now = self.get_clock().now()
        elapsed_s = (now - self._start_time).nanoseconds / 1e9
        dt_s = 0.0
        if self._previous_time is not None:
            dt_s = (now - self._previous_time).nanoseconds / 1e9
        self._previous_time = now

        speed_mps = sqrt(
            twist.linear.x * twist.linear.x
            + twist.linear.y * twist.linear.y
            + twist.linear.z * twist.linear.z
        )
        self._battery_percent = max(
            0.0,
            self._battery_percent
            - (self._battery_base_drain + self._battery_motion_drain * speed_mps)
            * dt_s,
        )

        state = UAVState(
            time_s=round(elapsed_s, 2),
            x_m=round(pose.position.x, 2),
            y_m=round(pose.position.y, 2),
            z_m=round(pose.position.z, 2),
            vx_mps=round(twist.linear.x, 2),
            vy_mps=round(twist.linear.y, 2),
            vz_mps=round(twist.linear.z, 2),
            battery_percent=round(self._battery_percent, 2),
            mission_state="GAZEBO_MODEL_STATE",
            frame_id="world",
        )

        output = state_to_msg(state, stamp=self.get_clock().now().to_msg())
        self._publisher.publish(output)


def main() -> None:
    rclpy.init()
    node = GazeboStateBridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
