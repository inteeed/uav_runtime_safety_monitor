# Safety Requirements

## Monitored State

Each UAV state log sample contains:

- mission time in seconds
- frame ID, currently `local_enu`
- position `x`, `y`, `z` in meters
- velocity `vx`, `vy`, `vz` in meters per second
- optional planned position `planned_x`, `planned_y`, `planned_z` in meters
- optional path deviation in meters
- battery percentage
- mission state
- safety status, severity, and recommended action
- supervisor mode and active response

## Safety Limits

| Requirement ID | Description | Limit | Status | Severity | Action |
| --- | --- | --- | --- | --- | --- |
| SR-001 | UAV shall warn before reaching the maximum altitude. | `z >= 25 m` and `z <= 30 m` | `ALTITUDE_WARNING` | `WARNING` | `WARNING` |
| SR-002 | UAV shall remain below the maximum allowed altitude. | `z <= 30 m` | `ALTITUDE_LIMIT_VIOLATION` | `CRITICAL` | `LAND` |
| SR-003 | UAV shall warn before leaving the mission geofence. | within `5 m` of boundary | `GEOFENCE_WARNING` | `WARNING` | `WARNING` |
| SR-004 | UAV shall remain inside the mission geofence. | `-50 <= x <= 50`, `-50 <= y <= 50` | `GEOFENCE_VIOLATION` | `CRITICAL` | `RETURN_TO_HOME` |
| SR-005 | UAV shall maintain sufficient battery reserve. | `battery >= 20%` | `LOW_BATTERY` | `CRITICAL` | `LAND` |
| SR-006 | UAV mission shall finish within the configured mission time. | `time <= 120 s` | `MISSION_TIMEOUT` | `CRITICAL` | `RETURN_TO_HOME` |
| SR-007 | UAV state updates shall arrive within the configured interval. | update gap `<= 2 s` | `STATE_TIMEOUT` | `CRITICAL` | `RETURN_TO_HOME` |
| SR-008 | UAV shall remain below the configured speed limit. | velocity magnitude `<= 10 m/s` | `VELOCITY_LIMIT_VIOLATION` | `CRITICAL` | `RETURN_TO_HOME` |
| SR-009 | UAV shall warn when it drifts away from the planned path. | path deviation `>= 5 m` and `<= 10 m` | `PATH_DEVIATION_WARNING` | `WARNING` | `WARNING` |
| SR-010 | UAV shall stay close to the planned path. | path deviation `<= 10 m` | `PATH_DEVIATION_VIOLATION` | `CRITICAL` | `RETURN_TO_HOME` |

## Validation Scenarios

| Scenario | Injected condition | Expected status | Expected action | Expected supervisor mode |
| --- | --- | --- | --- | --- |
| Normal mission | None | `SAFE` | `CONTINUE` | `CONTINUE_MISSION` |
| Geofence warning | UAV approaches geofence boundary | `GEOFENCE_WARNING` | `WARNING` | `WARNING_ACTIVE` |
| Geofence violation | UAV crosses `x = 50 m` boundary | `GEOFENCE_VIOLATION` | `RETURN_TO_HOME` | `RETURNING_HOME` |
| Unsafe geofence alias | Same geofence violation saved as `unsafe_mission.csv` | `GEOFENCE_VIOLATION` | `RETURN_TO_HOME` | `RETURNING_HOME` |
| Altitude violation | UAV climbs above `30 m` | `ALTITUDE_LIMIT_VIOLATION` | `LAND` | `LANDING` |
| Low battery | Battery drops below `20%` | `LOW_BATTERY` | `LAND` | `LANDING` |
| Mission timeout | Mission lasts longer than `120 s` | `MISSION_TIMEOUT` | `RETURN_TO_HOME` | `RETURNING_HOME` |
| State timeout | Simulated state-update gap exceeds `2 s` | `STATE_TIMEOUT` | `RETURN_TO_HOME` | `RETURNING_HOME` |
| Velocity violation | UAV speed exceeds `10 m/s` | `VELOCITY_LIMIT_VIOLATION` | `RETURN_TO_HOME` | `RETURNING_HOME` |
| Path deviation | UAV drifts `12 m` away from planned waypoint path | `PATH_DEVIATION_VIOLATION` | `RETURN_TO_HOME` | `RETURNING_HOME` |

The expected result for each scenario is encoded in `src/scenario_catalog.py` and checked by `analysis/validate_scenarios.py`.

## Event Logging

The monitor writes continuous state logs and separate event logs. Event logs record transitions such as `ENTERED_WARNING`, `ENTERED_VIOLATION`, `CHANGED_STATUS`, and `CLEARED_EVENT`. State logs also include supervisor fields such as `supervisor_mode`, `active_response`, and `response_reason`. This keeps flight-test-style analysis concise while preserving the full state and response history.

## Notes

The first version is a deterministic simulation. Later versions can make the path-deviation check more realistic by computing cross-track and along-track error against mission segments rather than using the simulated reference point stored in each state sample. Sensor dropouts, GPS quality, and obstacle proximity remain useful extensions.
