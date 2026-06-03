import sys

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)

from uav_safety_core.px4_commands import append_command_record, command_for_response
from uav_runtime_safety_monitor.ros2_messages import (
    SupervisorResponseMsg,
    ensure_typed_messages_available,
)


def _px4_command_qos() -> QoSProfile:
    return QoSProfile(
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.TRANSIENT_LOCAL,
        history=HistoryPolicy.KEEP_LAST,
        depth=10,
    )


class PX4CommandBridgeNode(Node):
    """Closes the safety loop by forwarding supervisor responses to PX4.

    This node turns a supervisor ``RETURN_TO_HOME`` / ``LAND`` response into a
    PX4 ``VehicleCommand``. It is deliberately **disabled by default**: actually
    commanding the vehicle is only safe in SITL or on a properly supervised test
    stand, so it must be explicitly enabled with ``enable_commands:=true``.
    While disabled it logs the command it *would* have sent, which is enough for
    wiring up and reviewing the loop without any risk of moving an aircraft.
    """

    def __init__(self) -> None:
        super().__init__("px4_command_bridge_node")
        ensure_typed_messages_available(self.get_logger())

        self.declare_parameter("enable_commands", False)
        self.declare_parameter("command_topic", "/fmu/in/vehicle_command")
        self.declare_parameter("supervisor_topic", "/uav/supervisor_mode")
        self.declare_parameter("target_system", 1)
        self.declare_parameter("target_component", 1)
        self.declare_parameter("command_log_path", "")

        self._enabled = bool(self.get_parameter("enable_commands").value)
        command_topic = str(self.get_parameter("command_topic").value)
        supervisor_topic = str(self.get_parameter("supervisor_topic").value)
        self._target_system = int(self.get_parameter("target_system").value)
        self._target_component = int(self.get_parameter("target_component").value)
        self._command_log_path = str(self.get_parameter("command_log_path").value)
        self._last_sent_response = None

        self._vehicle_command_cls = None
        if self._enabled:
            try:
                from px4_msgs.msg import VehicleCommand
            except ImportError as error:
                self.get_logger().error(
                    "enable_commands is true but px4_msgs is not available. "
                    "Build/source a PX4 ROS2 workspace containing px4_msgs."
                )
                raise error
            self._vehicle_command_cls = VehicleCommand
            self._command_publisher = self.create_publisher(
                VehicleCommand, command_topic, _px4_command_qos()
            )

        self._subscription = self.create_subscription(
            SupervisorResponseMsg,
            supervisor_topic,
            self._on_supervisor_response,
            10,
        )

        if self._enabled:
            self.get_logger().warn(
                "PX4 command bridge ARMED: supervisor responses will be sent "
                "to {} as PX4 VehicleCommands. Use in SITL / on a test stand "
                "only.".format(command_topic)
            )
        else:
            self.get_logger().info(
                "PX4 command bridge ready in DRY-RUN mode (enable_commands "
                "is false); commands are logged but not sent."
            )

    def _on_supervisor_response(self, message: SupervisorResponseMsg) -> None:
        response = str(message.active_response)
        command = command_for_response(response)
        if command is None:
            return

        # Send each distinct response only once, when it first activates.
        if response == self._last_sent_response:
            return
        self._last_sent_response = response

        if not self._enabled:
            self.get_logger().info(
                "[dry-run] would send PX4 command {} for supervisor "
                "response {}".format(command, response)
            )
            return

        self._publish_vehicle_command(command, response, float(message.time_s))

    def _publish_vehicle_command(
        self, command: int, response: str, time_s: float
    ) -> None:
        message = self._vehicle_command_cls()
        message.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        message.command = command
        message.target_system = self._target_system
        message.target_component = self._target_component
        message.source_system = self._target_system
        message.source_component = self._target_component
        message.from_external = True
        self._command_publisher.publish(message)
        self.get_logger().warn(
            "Sent PX4 command {} for supervisor response {}".format(
                command, response
            )
        )
        if self._command_log_path:
            append_command_record(
                self._command_log_path, time_s, response, command
            )


def main() -> int:
    rclpy.init()
    try:
        node = PX4CommandBridgeNode()
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
