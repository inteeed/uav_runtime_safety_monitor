import csv
from pathlib import Path
from typing import Optional, TextIO

from uav_runtime_safety_monitor.runtime_paths import add_runtime_paths


add_runtime_paths()

from logger import EVENT_FIELDNAMES, STATE_FIELDNAMES
from mission_simulator import UAVState
from mission_supervisor import SupervisorDecision, default_supervisor_decision
from safety_monitor import SafetyResult


class LiveLogWriter:
    """Streams ROS2 monitor output into mission and event CSV files."""

    def __init__(self, mission_log_path: Path, event_log_path: Path) -> None:
        self.mission_log_path = mission_log_path
        self.event_log_path = event_log_path
        self.sample_count = 0
        self.event_count = 0
        self._previous_result = SafetyResult(
            "SAFE", "CONTINUE", "INFO", "Initial monitor state"
        )
        self._mission_handle: Optional[TextIO] = None
        self._event_handle: Optional[TextIO] = None
        self._mission_writer: Optional[csv.DictWriter] = None
        self._event_writer: Optional[csv.DictWriter] = None

    def open(self) -> None:
        self.mission_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.event_log_path.parent.mkdir(parents=True, exist_ok=True)
        self._mission_handle = self.mission_log_path.open(
            "w", newline="", encoding="utf-8"
        )
        self._event_handle = self.event_log_path.open(
            "w", newline="", encoding="utf-8"
        )
        self._mission_writer = csv.DictWriter(
            self._mission_handle, fieldnames=STATE_FIELDNAMES
        )
        self._event_writer = csv.DictWriter(
            self._event_handle, fieldnames=EVENT_FIELDNAMES
        )
        self._mission_writer.writeheader()
        self._event_writer.writeheader()
        self._mission_handle.flush()
        self._event_handle.flush()

    def close(self) -> None:
        if self._mission_handle is not None:
            self._mission_handle.close()
            self._mission_handle = None
        if self._event_handle is not None:
            self._event_handle.close()
            self._event_handle = None

    def record(
        self,
        state: UAVState,
        result: SafetyResult,
        decision: SupervisorDecision = None,
    ) -> None:
        if self._mission_writer is None or self._event_writer is None:
            raise RuntimeError("LiveLogWriter.open() must be called before record().")

        decision = decision or default_supervisor_decision()
        self._mission_writer.writerow(
            self._state_row(state, result, decision)
        )
        self.sample_count += 1

        event_type = self._event_type(result)
        if event_type is not None:
            row = self._state_row(state, result, decision)
            row["event_type"] = event_type
            self._event_writer.writerow(
                {field: row[field] for field in EVENT_FIELDNAMES}
            )
            self.event_count += 1

        self._previous_result = result
        self._mission_handle.flush()
        self._event_handle.flush()

    def _event_type(self, result: SafetyResult) -> Optional[str]:
        if result.safety_status == self._previous_result.safety_status:
            return None

        if result.safety_status == "SAFE":
            return "CLEARED_EVENT"

        if self._previous_result.safety_status == "SAFE":
            if result.severity == "WARNING":
                return "ENTERED_WARNING"
            return "ENTERED_VIOLATION"

        return "CHANGED_STATUS"

    def _state_row(
        self,
        state: UAVState,
        result: SafetyResult,
        decision: SupervisorDecision,
    ) -> dict:
        return {
            "time_s": state.time_s,
            "frame_id": state.frame_id,
            "x_m": state.x_m,
            "y_m": state.y_m,
            "z_m": state.z_m,
            "vx_mps": state.vx_mps,
            "vy_mps": state.vy_mps,
            "vz_mps": state.vz_mps,
            "battery_percent": state.battery_percent,
            "mission_state": state.mission_state,
            "safety_status": result.safety_status,
            "severity": result.severity,
            "recommended_action": result.recommended_action,
            "supervisor_mode": decision.supervisor_mode,
            "active_response": decision.active_response,
            "response_reason": decision.response_reason,
            "detail": result.detail,
        }
