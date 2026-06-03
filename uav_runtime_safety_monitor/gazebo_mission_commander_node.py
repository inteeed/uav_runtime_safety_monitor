import rclpy
from rclpy.node import Node
from gazebo_msgs.msg import EntityState
from gazebo_msgs.srv import SetEntityState


from uav_safety_core.mission_simulator import MissionSimulator, UAVState
from uav_safety_core.mission_supervisor import MissionSupervisor
from uav_runtime_safety_monitor.ros2_messages import (
    SupervisorResponseMsg,
    ensure_typed_messages_available,
    supervisor_decision_from_msg,
)


class GazeboMissionCommanderNode(Node):
    """Moves the Gazebo UAV model through a scenario and reacts to supervisor mode."""

    def __init__(self) -> None:
        super().__init__("gazebo_mission_commander_node")
        ensure_typed_messages_available(self.get_logger())
        self.declare_parameter("model_name", "safety_uav")
        self.declare_parameter("scenario", "geofence_violation")
        self.declare_parameter("command_period_s", 0.5)

        self._model_name = str(self.get_parameter("model_name").value)
        scenario = str(self.get_parameter("scenario").value)
        command_period_s = float(self.get_parameter("command_period_s").value)

        self._states = MissionSimulator().generate(scenario)
        self._index = 0
        self._current_state = self._states[0]
        self._response_inserted = False
        self._supervisor = MissionSupervisor()

        self._client = self.create_client(SetEntityState, "/set_entity_state")
        self._subscription = self.create_subscription(
            SupervisorResponseMsg, "/uav/supervisor_mode", self._on_supervisor_mode, 10
        )
        self._timer = self.create_timer(command_period_s, self._send_next_state)
        self.get_logger().info(
            "Commanding Gazebo model '{}' with scenario '{}'".format(
                self._model_name, scenario
            )
        )

    def _on_supervisor_mode(self, message: SupervisorResponseMsg) -> None:
        if self._response_inserted:
            return

        decision = supervisor_decision_from_msg(message)
        if decision.active_response not in ("RETURN_TO_HOME", "LAND"):
            return

        response_states = self._supervisor.generate_response_states(
            self._current_state, decision
        )
        if not response_states:
            return

        self._states = self._states[: self._index] + response_states
        self._response_inserted = True
        self.get_logger().info(
            "Inserted supervisor response '{}' because of {}".format(
                decision.active_response, decision.response_reason
            )
        )

    def _send_next_state(self) -> None:
        if not self._client.service_is_ready():
            self._client.wait_for_service(timeout_sec=0.1)
            return

        if self._index >= len(self._states):
            self.get_logger().info("Gazebo mission command sequence complete")
            self._timer.cancel()
            return

        state = self._states[self._index]
        self._current_state = state
        request = SetEntityState.Request()
        request.state = self._to_entity_state(state)
        self._client.call_async(request)
        self.get_logger().info(
            "command {} t={:.1f}s x={:.1f} y={:.1f} z={:.1f}".format(
                state.mission_state,
                state.time_s,
                state.x_m,
                state.y_m,
                state.z_m,
            )
        )
        self._index += 1

    def _to_entity_state(self, state: UAVState) -> EntityState:
        entity_state = EntityState()
        entity_state.name = self._model_name
        entity_state.reference_frame = "world"
        entity_state.pose.position.x = float(state.x_m)
        entity_state.pose.position.y = float(state.y_m)
        entity_state.pose.position.z = float(state.z_m)
        entity_state.pose.orientation.w = 1.0
        entity_state.twist.linear.x = float(state.vx_mps)
        entity_state.twist.linear.y = float(state.vy_mps)
        entity_state.twist.linear.z = float(state.vz_mps)
        return entity_state


def main() -> None:
    rclpy.init()
    node = GazeboMissionCommanderNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
