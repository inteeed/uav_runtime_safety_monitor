from dataclasses import dataclass
from math import ceil, sqrt
from typing import List

from mission_simulator import UAVState
from safety_monitor import SafetyResult


@dataclass(frozen=True)
class SupervisorDecision:
    supervisor_mode: str
    active_response: str
    response_reason: str
    response_started: bool = False


def default_supervisor_decision() -> SupervisorDecision:
    return SupervisorDecision(
        supervisor_mode="CONTINUE_MISSION",
        active_response="NONE",
        response_reason="No supervisor action active",
        response_started=False,
    )


class MissionSupervisor:
    """Converts safety-monitor outputs into high-level mission response modes."""

    def __init__(
        self,
        dt_s: float = 1.0,
        return_speed_mps: float = 5.0,
        landing_rate_mps: float = 2.0,
        battery_base_drain_percent_per_s: float = 0.055,
        battery_motion_drain_percent_per_s: float = 0.012,
    ) -> None:
        self.dt_s = dt_s
        self.return_speed_mps = return_speed_mps
        self.landing_rate_mps = landing_rate_mps
        self.battery_base_drain_percent_per_s = battery_base_drain_percent_per_s
        self.battery_motion_drain_percent_per_s = battery_motion_drain_percent_per_s
        self._mode = "CONTINUE_MISSION"
        self._active_response = "NONE"
        self._response_reason = "No supervisor action active"

    def update(self, state: UAVState, result: SafetyResult) -> SupervisorDecision:
        if state.mission_state == "RESPONSE_COMPLETE":
            self._mode = "RESPONSE_COMPLETE"
            self._active_response = "NONE"
            self._response_reason = "Supervisor response completed"
            return SupervisorDecision(
                self._mode, self._active_response, self._response_reason
            )

        if self._mode in ("RETURNING_HOME", "LANDING", "MISSION_ABORTED"):
            return SupervisorDecision(
                self._mode, self._active_response, self._response_reason
            )

        if result.recommended_action == "RETURN_TO_HOME":
            self._mode = "RETURNING_HOME"
            self._active_response = "RETURN_TO_HOME"
            self._response_reason = result.safety_status
            return SupervisorDecision(
                self._mode,
                self._active_response,
                self._response_reason,
                response_started=True,
            )

        if result.recommended_action == "LAND":
            self._mode = "LANDING"
            self._active_response = "LAND"
            self._response_reason = result.safety_status
            return SupervisorDecision(
                self._mode,
                self._active_response,
                self._response_reason,
                response_started=True,
            )

        if result.recommended_action == "ABORT_MISSION":
            self._mode = "MISSION_ABORTED"
            self._active_response = "ABORT_MISSION"
            self._response_reason = result.safety_status
            return SupervisorDecision(
                self._mode,
                self._active_response,
                self._response_reason,
                response_started=True,
            )

        if result.severity == "WARNING":
            self._mode = "WARNING_ACTIVE"
            self._active_response = "MONITOR"
            self._response_reason = result.safety_status
            return SupervisorDecision(
                self._mode, self._active_response, self._response_reason
            )

        self._mode = "CONTINUE_MISSION"
        self._active_response = "NONE"
        self._response_reason = "No supervisor action active"
        return SupervisorDecision(
            self._mode, self._active_response, self._response_reason
        )

    def generate_response_states(
        self, start: UAVState, decision: SupervisorDecision
    ) -> List[UAVState]:
        if decision.active_response == "RETURN_TO_HOME":
            return self._return_home_response(start)
        if decision.active_response == "LAND":
            return self._landing_response(start)
        return []

    def _return_home_response(self, start: UAVState) -> List[UAVState]:
        states = self._travel(
            start,
            target=(0.0, 0.0, start.z_m),
            speed_mps=self.return_speed_mps,
            mission_state="RESPONSE_RETURN_HOME",
        )
        current = states[-1] if states else start
        states.extend(
            self._travel(
                current,
                target=(0.0, 0.0, 0.0),
                speed_mps=self.landing_rate_mps,
                mission_state="RESPONSE_LANDING",
            )
        )
        current = states[-1] if states else current
        states.append(self._complete_state(current))
        return states

    def _landing_response(self, start: UAVState) -> List[UAVState]:
        states = self._travel(
            start,
            target=(start.x_m, start.y_m, 0.0),
            speed_mps=self.landing_rate_mps,
            mission_state="RESPONSE_LANDING",
        )
        current = states[-1] if states else start
        states.append(self._complete_state(current))
        return states

    def _travel(
        self,
        start: UAVState,
        target,
        speed_mps: float,
        mission_state: str,
    ) -> List[UAVState]:
        dx = target[0] - start.x_m
        dy = target[1] - start.y_m
        dz = target[2] - start.z_m
        distance_m = sqrt(dx * dx + dy * dy + dz * dz)
        if distance_m == 0.0:
            return []

        duration_s = distance_m / speed_mps
        steps = max(1, int(ceil(duration_s / self.dt_s)))
        step_duration_s = duration_s / steps

        vx = dx / duration_s
        vy = dy / duration_s
        vz = dz / duration_s
        speed = sqrt(vx * vx + vy * vy + vz * vz)
        battery = start.battery_percent

        states: List[UAVState] = []
        for step in range(1, steps + 1):
            ratio = float(step) / float(steps)
            time_s = start.time_s + step * step_duration_s
            battery -= (
                self.battery_base_drain_percent_per_s
                + self.battery_motion_drain_percent_per_s * speed
            ) * step_duration_s
            states.append(
                UAVState(
                    round(time_s, 2),
                    round(start.x_m + ratio * dx, 2),
                    round(start.y_m + ratio * dy, 2),
                    round(start.z_m + ratio * dz, 2),
                    round(vx, 2),
                    round(vy, 2),
                    round(vz, 2),
                    round(max(0.0, battery), 2),
                    mission_state,
                    start.frame_id,
                )
            )

        return states

    def _complete_state(self, state: UAVState) -> UAVState:
        return UAVState(
            round(state.time_s + self.dt_s, 2),
            state.x_m,
            state.y_m,
            state.z_m,
            0.0,
            0.0,
            0.0,
            state.battery_percent,
            "RESPONSE_COMPLETE",
            state.frame_id,
        )

