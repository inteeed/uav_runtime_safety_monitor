# Safety Requirements

## Monitored State

Each UAV state sample contains:

- mission time
- position `x`, `y`, `z`
- velocity `vx`, `vy`, `vz`
- battery percentage
- mission state

## Safety Limits

| Requirement ID | Description | Limit | Status on violation | Action |
| --- | --- | --- | --- | --- |
| SR-001 | UAV shall remain below the maximum allowed altitude. | `z <= 30 m` | `ALTITUDE_LIMIT_VIOLATION` | `LAND` |
| SR-002 | UAV shall remain inside the mission geofence. | `-50 <= x <= 50`, `-50 <= y <= 50` | `GEOFENCE_VIOLATION` | `RETURN_TO_HOME` |
| SR-003 | UAV shall maintain sufficient battery reserve. | `battery >= 20%` | `LOW_BATTERY` | `LAND` |
| SR-004 | UAV mission shall finish within the configured mission time. | `time <= 120 s` | `MISSION_TIMEOUT` | `RETURN_TO_HOME` |

## Validation Scenarios

| Scenario | Injected fault | Expected status | Expected action |
| --- | --- | --- | --- |
| Normal mission | None | `SAFE` | `CONTINUE` |
| Unsafe geofence mission | UAV crosses `x = 50 m` boundary | `GEOFENCE_VIOLATION` | `RETURN_TO_HOME` |

## Notes

The first version is a deterministic simulation. Future versions can extend this with ROS2 state messages, PX4 SITL data, Gazebo simulation, sensor dropouts, and trajectory deviation checks.

