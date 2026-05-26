# PX4 Integration Plan

The PX4 extension should connect the existing runtime safety monitor to PX4 telemetry while preserving the same safety-monitoring interface used by the Python and Gazebo demos.

## Design Principle

The safety monitor should not depend directly on PX4 message types. PX4-specific code stays in a bridge:

```text
PX4 ROS2 topics -> px4_state_bridge -> /uav/state -> safety_monitor
```

This keeps the monitor reusable across:

- pure Python simulation,
- Gazebo kinematic simulation,
- PX4 SITL,
- future hardware telemetry.

## Implemented Bridge Boundary

The optional `px4_state_bridge` node subscribes to:

- `/fmu/out/vehicle_local_position`
- `/fmu/out/battery_status`

It publishes:

- `/uav/state`

The bridge is optional because it requires `px4_msgs`, which is provided by a PX4 ROS2 workspace rather than this repository.

## Supervisor Action Mapping

Current supervisor actions:

| Monitor action | Current project behavior | Future PX4 behavior |
| --- | --- | --- |
| `WARNING` | log and continue monitoring | log and optionally notify ground station |
| `RETURN_TO_HOME` | generate return-home response in simulation | send PX4 return/RTL command after validation |
| `LAND` | generate landing response in simulation | send PX4 land command after validation |
| `ABORT_MISSION` | enter abort mode | hold, land, or terminate according to test policy |

The future command bridge should be implemented only after state monitoring is validated with PX4 SITL.

## Risk Controls

PX4 command output should start disabled by default. A safe sequence is:

1. Read-only telemetry bridge.
2. Monitor-only safety status.
3. Log supervisor decisions without sending commands.
4. Enable command output only in SITL.
5. Add explicit arming/mode guards before any flight-test use.

## Acceptance Criteria

PX4 extension can be considered minimally working when:

- PX4 SITL publishes local position and battery topics,
- `px4_state_bridge` publishes `/uav/state`,
- `safety_monitor` detects an intentional violation,
- `mission_supervisor` publishes the expected response,
- the run is documented with logs or screenshots.
