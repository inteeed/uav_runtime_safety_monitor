# ROS2 Package Usage

This repository is also an `ament_python` ROS2 package named `uav_runtime_safety_monitor`.

The package provides ROS2 entry points for:

- `safety_monitor`
- `mission_supervisor`
- `uav_state_publisher`
- `gazebo_state_bridge`
- `gazebo_mission_commander`

It also installs Gazebo models, Gazebo worlds, safety configuration, and launch files.

## Build

Use a clean ROS2 Foxy terminal. Do not source ROS Noetic in the same shell.

```bash
cd /home/inteed/projects/uav-runtime-safety-monitor
source /opt/ros/foxy/setup.bash
colcon build --symlink-install --packages-select uav_runtime_safety_monitor
source install/setup.bash
```

## Launch Visible Gazebo Demo

```bash
ros2 launch uav_runtime_safety_monitor gazebo_safety_demo.launch.py
```

This starts:

- Gazebo Classic with the UAV safety demo world,
- Gazebo model-state bridge,
- runtime safety monitor,
- mission supervisor,
- Gazebo mission commander.

The default scenario is `geofence_violation`.

## Launch Headless Gazebo Demo

```bash
ros2 launch uav_runtime_safety_monitor gazebo_headless_safety_demo.launch.py
```

## Scenario Selection

```bash
ros2 launch uav_runtime_safety_monitor gazebo_safety_demo.launch.py scenario:=altitude_violation
ros2 launch uav_runtime_safety_monitor gazebo_safety_demo.launch.py scenario:=low_battery
ros2 launch uav_runtime_safety_monitor gazebo_safety_demo.launch.py scenario:=mission_timeout
```

## Topic Checks

```bash
ros2 topic list
ros2 topic echo /uav/state
ros2 topic echo /uav/safety_status
ros2 topic echo /uav/supervisor_mode
```

## Notes

The existing script-based demos in `gazebo_extension/` are still useful for automated log validation. The ROS2 package launch files are the recommended interface for demonstrating integration with a ROS2/Gazebo system.
