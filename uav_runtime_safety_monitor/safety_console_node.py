import json
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from uav_runtime_safety_monitor.runtime_paths import add_runtime_paths


add_runtime_paths()

from ros2_json import (
    safety_result_from_json,
    state_from_json,
    supervisor_decision_from_json,
)


class SafetyConsoleNode(Node):
    """Prints compact runtime safety status for live demos."""

    def __init__(self) -> None:
        super().__init__("safety_console_node")
        self.declare_parameter("print_period_s", 1.0)

        print_period_s = float(self.get_parameter("print_period_s").value)
        self._latest_state = None
        self._latest_result = None
        self._latest_decision = None
        self._last_status_key = None

        self.create_subscription(String, "/uav/state", self._on_state, 10)
        self.create_subscription(
            String, "/uav/safety_status", self._on_safety_status, 10
        )
        self.create_subscription(
            String, "/uav/supervisor_mode", self._on_supervisor_mode, 10
        )
        self.create_timer(max(0.2, print_period_s), self._print_snapshot)
        self.get_logger().info("Safety console ready")

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
            return

        status_key = (
            self._latest_result.safety_status,
            self._latest_result.severity,
            self._latest_result.recommended_action,
        )
        if status_key != self._last_status_key:
            self._last_status_key = status_key
            self._print_snapshot(force=True)

    def _on_supervisor_mode(self, message: String) -> None:
        try:
            self._latest_decision = supervisor_decision_from_json(message.data)
        except (json.JSONDecodeError, KeyError, ValueError) as error:
            self.get_logger().warn(
                "Could not parse /uav/supervisor_mode: {}".format(error)
            )

    def _print_snapshot(self, force: bool = False) -> None:
        if self._latest_result is None:
            return

        state_text = self._format_state()
        decision_text = self._format_decision()
        result = self._latest_result
        label = self._label_for_severity(result.severity)
        line = (
            "[{label}] status={status} action={action} {state} {decision} "
            "detail={detail}"
        ).format(
            label=label,
            status=result.safety_status,
            action=result.recommended_action,
            state=state_text,
            decision=decision_text,
            detail=result.detail,
        )

        if force or result.safety_status != "SAFE":
            print(line, flush=True)
        elif self._latest_state is not None:
            print(line, flush=True)

    def _format_state(self) -> str:
        if self._latest_state is None:
            return "pos=(unknown)"

        state = self._latest_state
        return (
            "t={:.1f}s pos=({:.1f},{:.1f},{:.1f}) "
            "vel=({:.1f},{:.1f},{:.1f}) batt={:.1f}%"
        ).format(
            state.time_s,
            state.x_m,
            state.y_m,
            state.z_m,
            state.vx_mps,
            state.vy_mps,
            state.vz_mps,
            state.battery_percent,
        )

    def _format_decision(self) -> str:
        if self._latest_decision is None:
            return "supervisor=(unknown)"

        decision = self._latest_decision
        return "supervisor={} response={}".format(
            decision.supervisor_mode,
            decision.active_response,
        )

    def _label_for_severity(self, severity: Optional[str]) -> str:
        if severity == "CRITICAL":
            return "CRITICAL"
        if severity == "WARNING":
            return "WARNING"
        return "INFO"


def main() -> None:
    rclpy.init()
    node = SafetyConsoleNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
