#!/usr/bin/env python3
"""Fly PX4 SITL past the geofence so the monitor sees a *real* violation.

Unlike ``inject_monitor_violation.sh`` (which overwrites the state stream with a
synthetic fault), this commands PX4 over offboard control to actually fly to a
position outside the configured geofence. The safety monitor then detects the
breach from genuine ``/fmu/out/vehicle_local_position`` telemetry.

SITL / test-stand use only. Requires a PX4 ROS2 workspace providing ``px4_msgs``
and a running Micro XRCE-DDS Agent.

Sequence (standard PX4 offboard pattern):
  1. stream OffboardControlMode + TrajectorySetpoint at 10 Hz,
  2. after a short warm-up, command OFFBOARD mode and arm,
  3. hold a setpoint beyond the geofence boundary until timeout.
"""

import argparse
import sys

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)


def _px4_qos() -> QoSProfile:
    return QoSProfile(
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.TRANSIENT_LOCAL,
        history=HistoryPolicy.KEEP_LAST,
        depth=10,
    )


class FlyBeyondGeofenceNode(Node):
    # Supervisor responses that mean "stop flying out, hand control back to PX4".
    _RELEASE_RESPONSES = ("RETURN_TO_HOME", "LAND")

    def __init__(self, target_x_m: float, target_y_m: float, altitude_m: float,
                 hold_s: float) -> None:
        super().__init__("fly_beyond_geofence_node")
        from px4_msgs.msg import (
            OffboardControlMode,
            TrajectorySetpoint,
            VehicleCommand,
        )

        self._OffboardControlMode = OffboardControlMode
        self._TrajectorySetpoint = TrajectorySetpoint
        self._VehicleCommand = VehicleCommand

        self._target = (target_x_m, target_y_m, -abs(altitude_m))  # PX4 NED: down<0
        self._hold_s = hold_s
        self._tick = 0
        self._released = False

        qos = _px4_qos()
        self._offboard_pub = self.create_publisher(
            OffboardControlMode, "/fmu/in/offboard_control_mode", qos
        )
        self._setpoint_pub = self.create_publisher(
            TrajectorySetpoint, "/fmu/in/trajectory_setpoint", qos
        )
        self._command_pub = self.create_publisher(
            VehicleCommand, "/fmu/in/vehicle_command", qos
        )

        # Watch the supervisor so we can release offboard control the moment a
        # safety response fires, letting PX4 execute RTL/Land instead of us
        # fighting it with more outbound setpoints. The typed message is only
        # available once the monitor workspace is sourced; if not, the node
        # still flies out and relies on the --hold timeout.
        try:
            from uav_runtime_safety_monitor_msgs.msg import SupervisorResponse

            self.create_subscription(
                SupervisorResponse,
                "/uav/supervisor_mode",
                self._on_supervisor_response,
                10,
            )
        except ImportError:
            self.get_logger().warn(
                "uav_runtime_safety_monitor_msgs not available; flying out "
                "without supervisor handoff (will stop after --hold seconds)."
            )

        self._period_s = 0.1  # 10 Hz
        self.create_timer(self._period_s, self._on_timer)
        self.get_logger().warn(
            "Flying PX4 toward ({:.1f}, {:.1f}, {:.1f}) m to breach the "
            "geofence. SITL only.".format(*self._target)
        )

    def _on_supervisor_response(self, message) -> None:
        if self._released:
            return
        if str(message.active_response) in self._RELEASE_RESPONSES:
            self._released = True
            self.get_logger().warn(
                "Supervisor response {} detected; releasing offboard control "
                "so PX4 can execute it.".format(message.active_response)
            )

    def _timestamp(self) -> int:
        return int(self.get_clock().now().nanoseconds / 1000)

    def _send_vehicle_command(self, command: int, param1: float = 0.0,
                              param2: float = 0.0) -> None:
        msg = self._VehicleCommand()
        msg.timestamp = self._timestamp()
        msg.command = command
        msg.param1 = param1
        msg.param2 = param2
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        self._command_pub.publish(msg)

    def _on_timer(self) -> None:
        # Once the supervisor has responded, stop publishing offboard setpoints.
        # PX4 drops out of offboard after ~0.5 s without setpoints, letting the
        # RTL/Land command issued by the command bridge take effect.
        if self._released:
            self.get_logger().info(
                "Offboard control released; PX4 should now execute the safety "
                "response. Stopping commander."
            )
            rclpy.shutdown()
            return

        offboard = self._OffboardControlMode()
        offboard.timestamp = self._timestamp()
        offboard.position = True
        self._offboard_pub.publish(offboard)

        setpoint = self._TrajectorySetpoint()
        setpoint.timestamp = self._timestamp()
        setpoint.position = [float(v) for v in self._target]
        self._setpoint_pub.publish(setpoint)

        # After ~1 s of setpoints, switch to OFFBOARD (base mode custom, main 6)
        # and arm, as required before PX4 accepts offboard control.
        if self._tick == 10:
            self._send_vehicle_command(
                self._VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
                param1=1.0,
                param2=6.0,
            )
            self._send_vehicle_command(
                self._VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,
                param1=1.0,
            )
            self.get_logger().info("Commanded OFFBOARD + arm.")

        self._tick += 1
        if self._tick * self._period_s >= self._hold_s:
            self.get_logger().info("Hold time elapsed; stopping commander.")
            rclpy.shutdown()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-x", type=float, default=60.0,
                        help="Target X in metres (geofence x_max is 50 m).")
    parser.add_argument("--target-y", type=float, default=0.0)
    parser.add_argument("--altitude", type=float, default=5.0,
                        help="Flight altitude in metres (positive up).")
    parser.add_argument("--hold", type=float, default=30.0,
                        help="Seconds to stream setpoints before stopping.")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    rclpy.init()
    try:
        node = FlyBeyondGeofenceNode(
            args.target_x, args.target_y, args.altitude, args.hold
        )
    except ImportError:
        print("px4_msgs is required. Source a PX4 ROS2 workspace first.",
              file=sys.stderr)
        rclpy.shutdown()
        return 2

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
