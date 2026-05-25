import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mission_simulator import UAVState
from safety_monitor import SafetyResult
from mission_supervisor import SupervisorDecision


def state_to_json(state: UAVState) -> str:
    return json.dumps(
        {
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
        },
        sort_keys=True,
    )


def state_from_json(payload: str) -> UAVState:
    data = json.loads(payload)
    return UAVState(
        time_s=float(data["time_s"]),
        x_m=float(data["x_m"]),
        y_m=float(data["y_m"]),
        z_m=float(data["z_m"]),
        vx_mps=float(data.get("vx_mps", 0.0)),
        vy_mps=float(data.get("vy_mps", 0.0)),
        vz_mps=float(data.get("vz_mps", 0.0)),
        battery_percent=float(data["battery_percent"]),
        mission_state=str(data["mission_state"]),
        frame_id=str(data.get("frame_id", "local_enu")),
    )


def safety_result_to_json(result: SafetyResult) -> str:
    return json.dumps(
        {
            "safety_status": result.safety_status,
            "severity": result.severity,
            "recommended_action": result.recommended_action,
            "detail": result.detail,
        },
        sort_keys=True,
    )


def safety_result_from_json(payload: str) -> SafetyResult:
    data = json.loads(payload)
    return SafetyResult(
        safety_status=str(data["safety_status"]),
        recommended_action=str(data["recommended_action"]),
        severity=str(data["severity"]),
        detail=str(data.get("detail", "")),
    )


def supervisor_decision_to_json(decision: SupervisorDecision) -> str:
    return json.dumps(
        {
            "supervisor_mode": decision.supervisor_mode,
            "active_response": decision.active_response,
            "response_reason": decision.response_reason,
            "response_started": decision.response_started,
        },
        sort_keys=True,
    )

