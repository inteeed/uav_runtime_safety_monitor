import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

from mission_simulator import UAVState
from safety_monitor import SafetyResult


STATE_FIELDNAMES = [
    "time_s",
    "frame_id",
    "x_m",
    "y_m",
    "z_m",
    "vx_mps",
    "vy_mps",
    "vz_mps",
    "battery_percent",
    "mission_state",
    "safety_status",
    "severity",
    "recommended_action",
    "detail",
]

EVENT_FIELDNAMES = [
    "time_s",
    "event_type",
    "frame_id",
    "x_m",
    "y_m",
    "z_m",
    "battery_percent",
    "mission_state",
    "safety_status",
    "severity",
    "recommended_action",
    "detail",
]


@dataclass(frozen=True)
class SafetyEvent:
    state: UAVState
    result: SafetyResult
    event_type: str


def write_mission_log(
    path: Path, records: Iterable[Tuple[UAVState, SafetyResult]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=STATE_FIELDNAMES)
        writer.writeheader()
        for state, result in records:
            writer.writerow(
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
                    "safety_status": result.safety_status,
                    "severity": result.severity,
                    "recommended_action": result.recommended_action,
                    "detail": result.detail,
                }
            )


def extract_safety_events(
    records: Iterable[Tuple[UAVState, SafetyResult]]
) -> List[SafetyEvent]:
    events: List[SafetyEvent] = []
    previous_result: SafetyResult = SafetyResult(
        "SAFE", "CONTINUE", "INFO", "Initial monitor state"
    )

    for state, result in records:
        if result.safety_status == previous_result.safety_status:
            previous_result = result
            continue

        if result.safety_status == "SAFE":
            event_type = "CLEARED_EVENT"
        elif previous_result.safety_status == "SAFE":
            if result.severity == "WARNING":
                event_type = "ENTERED_WARNING"
            else:
                event_type = "ENTERED_VIOLATION"
        else:
            event_type = "CHANGED_STATUS"

        events.append(SafetyEvent(state=state, result=result, event_type=event_type))
        previous_result = result

    return events


def write_event_log(path: Path, events: Iterable[SafetyEvent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EVENT_FIELDNAMES)
        writer.writeheader()
        for event in events:
            state = event.state
            result = event.result
            writer.writerow(
                {
                    "time_s": state.time_s,
                    "event_type": event.event_type,
                    "frame_id": state.frame_id,
                    "x_m": state.x_m,
                    "y_m": state.y_m,
                    "z_m": state.z_m,
                    "battery_percent": state.battery_percent,
                    "mission_state": state.mission_state,
                    "safety_status": result.safety_status,
                    "severity": result.severity,
                    "recommended_action": result.recommended_action,
                    "detail": result.detail,
                }
            )

