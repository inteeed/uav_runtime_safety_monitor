import json
from dataclasses import replace
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


from uav_safety_core.mission_simulator import UAVState
from uav_runtime_safety_monitor.ros2_messages import (
    UAVStateMsg,
    ensure_typed_messages_available,
    state_from_msg,
    state_to_msg,
)


class FaultInjectionNode(Node):
    """Applies short synthetic faults to a single UAV state stream."""

    def __init__(self) -> None:
        super().__init__("fault_injection_node")
        ensure_typed_messages_available(self.get_logger())
        self.declare_parameter("input_topic", "/uav/raw_state")
        self.declare_parameter("output_topic", "/uav/state")
        self.declare_parameter("command_topic", "/uav/fault_injection")

        input_topic = str(self.get_parameter("input_topic").value)
        output_topic = str(self.get_parameter("output_topic").value)
        command_topic = str(self.get_parameter("command_topic").value)

        self._active_scenario: Optional[str] = None
        self._active_until_ns: Optional[int] = None
        self._publisher = self.create_publisher(UAVStateMsg, output_topic, 10)
        self.create_subscription(UAVStateMsg, input_topic, self._on_state, 10)
        self.create_subscription(String, command_topic, self._on_command, 10)
        self.get_logger().info(
            "Fault injector ready: {} -> {}; commands on {}".format(
                input_topic,
                output_topic,
                command_topic,
            )
        )

    def _on_command(self, message: String) -> None:
        try:
            data = json.loads(message.data)
            scenario = str(data["scenario"]).lower()
            duration_s = float(data.get("duration_s", 6.0))
        except (json.JSONDecodeError, KeyError, ValueError) as error:
            self.get_logger().warn(
                "Could not parse /uav/fault_injection command: {}".format(error)
            )
            return

        if scenario not in ("geofence", "altitude", "battery"):
            self.get_logger().warn(
                "Unsupported fault scenario '{}'. Use geofence, altitude, or battery.".format(
                    scenario
                )
            )
            return

        now = self.get_clock().now().nanoseconds
        self._active_scenario = scenario
        self._active_until_ns = now + int(max(0.1, duration_s) * 1e9)
        self.get_logger().info(
            "Activated {} fault injection for {:.1f} s".format(
                scenario,
                duration_s,
            )
        )

    def _on_state(self, message: UAVStateMsg) -> None:
        state = state_from_msg(message)
        output_state = self._apply_fault_if_active(state)
        output = state_to_msg(output_state, stamp=self.get_clock().now().to_msg())
        self._publisher.publish(output)

    def _apply_fault_if_active(self, state: UAVState) -> UAVState:
        if self._active_scenario is None or self._active_until_ns is None:
            return state

        now = self.get_clock().now().nanoseconds
        if now > self._active_until_ns:
            self.get_logger().info(
                "Cleared {} fault injection".format(self._active_scenario)
            )
            self._active_scenario = None
            self._active_until_ns = None
            return state

        if self._active_scenario == "geofence":
            return replace(
                state,
                x_m=60.0,
                y_m=0.0,
                mission_state="PX4_FAULT_GEOFENCE_TEST",
                frame_id="px4_local_ned_fault_injected",
            )

        if self._active_scenario == "altitude":
            return replace(
                state,
                z_m=35.0,
                mission_state="PX4_FAULT_ALTITUDE_TEST",
                frame_id="px4_local_ned_fault_injected",
            )

        if self._active_scenario == "battery":
            return replace(
                state,
                battery_percent=10.0,
                mission_state="PX4_FAULT_LOW_BATTERY_TEST",
                frame_id="px4_local_ned_fault_injected",
            )

        return state


def main() -> None:
    rclpy.init()
    node = FaultInjectionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
