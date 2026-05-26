# PX4 Extension

This folder documents the planned PX4 SITL integration for the runtime safety monitor.

The current repository already has:

- pure Python scenario validation,
- ROS2 nodes,
- Gazebo Classic simulation,
- automated Gazebo integration validation,
- ROS2 package launch files.

The PX4 extension should reuse the same safety-monitoring interface instead of replacing the project with a full autopilot stack.

## Integration Goal

```text
PX4 SITL telemetry
        |
        v
px4_state_bridge
        |
        v
/uav/state
        |
        v
safety_monitor
        |
        v
/uav/safety_status + /uav/recommended_action
        |
        v
mission_supervisor
        |
        v
/uav/supervisor_mode
```

The safety monitor remains independent from PX4. Only the state source changes.

## Current Status

Implemented in the ROS2 package:

- `px4_state_bridge` console entry point,
- `px4_environment_check` console entry point,
- `px4_safety_monitor.launch.py`,
- PX4 local-position to monitor-state conversion helpers,
- PX4 readiness checks for mixed ROS environments and required ROS2 packages,
- tests for the NED-to-positive-altitude mapping.

Not implemented yet:

- PX4 SITL startup inside this repository,
- command feedback from `/uav/supervisor_mode` into PX4 failsafe commands,
- flight-mode switching,
- offboard trajectory control.

## Required PX4 ROS2 Inputs

The bridge expects these PX4 ROS2 topics:

| PX4 topic | PX4 message | Used for |
| --- | --- | --- |
| `/fmu/out/vehicle_local_position` | `px4_msgs/msg/VehicleLocalPosition` | local position and velocity |
| `/fmu/out/battery_status` | `px4_msgs/msg/BatteryStatus` | battery percentage |

The bridge publishes:

| Project topic | Message | Purpose |
| --- | --- | --- |
| `/uav/state` | `std_msgs/String` JSON payload | Existing safety-monitor input |

## Coordinate Mapping

PX4 local position uses NED convention:

```text
x = north
y = east
z = down
```

The safety monitor expects altitude as positive-up `z_m`, so the bridge maps:

```text
x_m = px4.x
y_m = px4.y
z_m = -px4.z
vx_mps = px4.vx
vy_mps = px4.vy
vz_mps = -px4.vz
```

This lets the existing altitude-limit rule keep working without changing monitor logic.

## Run After PX4 ROS2 Setup Exists

Use this only after a PX4 ROS2 workspace with `px4_msgs` is built and sourced.
Follow the official PX4 ROS2 user guide for `px4_msgs`, `px4_ros_com`, and DDS setup:

```text
https://docs.px4.io/main/en/ros2/user_guide.html
```

For PX4's current Gazebo SITL workflow, follow:

```text
https://docs.px4.io/main/en/sim_gazebo_gz/
```

```bash
source /opt/ros/foxy/setup.bash
source <px4_ros2_ws>/install/setup.bash
cd /home/inteed/projects/uav-runtime-safety-monitor
python3 px4_extension/check_px4_environment.py --extra-setup <px4_ros2_ws>/install/setup.bash --strict
colcon build --symlink-install --packages-select uav_runtime_safety_monitor
source install/setup.bash
ros2 launch uav_runtime_safety_monitor px4_safety_monitor.launch.py
```

The helper script combines those project-side steps:

```bash
export PX4_ROS2_WS_SETUP=<px4_ros2_ws>/install/setup.bash
./px4_extension/run_px4_monitor_stack.sh
```

Use the live topic check only after PX4 SITL and the Micro XRCE-DDS Agent are running:

```bash
python3 px4_extension/check_px4_environment.py --extra-setup <px4_ros2_ws>/install/setup.bash --check-topics --strict
```

In another terminal, PX4 SITL and the ROS2/DDS bridge must be running according to the PX4 ROS2 documentation.

## Validation Checklist

Before claiming PX4 integration is working, verify:

- `ros2 topic list` shows `/fmu/out/vehicle_local_position`,
- `ros2 topic list` shows `/fmu/out/battery_status`,
- `ros2 topic echo /uav/state` shows JSON state messages,
- `ros2 topic echo /uav/safety_status` shows monitor output,
- a controlled geofence or altitude violation produces the expected supervisor response.

## Why This Is Experimental

The project currently uses ROS2 Foxy and Gazebo Classic for the validated demo. Current PX4 SITL setups often use newer Gazebo versions and additional PX4 ROS2 tooling. Keeping PX4 as an extension avoids making the working safety-monitoring demo dependent on a fragile autopilot installation.
