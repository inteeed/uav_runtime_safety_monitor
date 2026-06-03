# ROS2 Package Usage

This repository includes two ROS2 packages:

- `uav_runtime_safety_monitor_msgs`: custom message interfaces.
- `uav_runtime_safety_monitor`: Python runtime nodes and launch files.

The package provides ROS2 entry points for:

- `safety_monitor`
- `mission_supervisor`
- `uav_state_publisher`
- `gazebo_state_bridge`
- `gazebo_mission_commander`
- `px4_state_bridge` experimental, requires `px4_msgs`
- `px4_environment_check` PX4/ROS2 readiness check

It also installs Gazebo models, Gazebo worlds, safety configuration, and launch files.

## Message Interfaces

The packaged ROS2 stack uses typed topics instead of JSON strings:

| Topic | Message |
| --- | --- |
| `/uav/state` | `uav_runtime_safety_monitor_msgs/msg/UAVState` |
| `/uav/safety_status` | `uav_runtime_safety_monitor_msgs/msg/SafetyStatus` |
| `/uav/supervisor_mode` | `uav_runtime_safety_monitor_msgs/msg/SupervisorResponse` |
| `/uav/recommended_action` | `std_msgs/msg/String` convenience topic |

## Build

Use a clean ROS2 Foxy terminal. Do not source ROS Noetic in the same shell.

```bash
cd /home/inteed/projects/uav-runtime-safety-monitor
source /opt/ros/$ROS_DISTRO/setup.bash
colcon build --symlink-install --base-paths . interfaces/uav_runtime_safety_monitor_msgs --packages-up-to uav_runtime_safety_monitor
source install/setup.bash
```

The explicit `--base-paths` argument is intentional: the repository root is the
Python package, while the message package lives under `interfaces/`.

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

## Optional PX4 Monitor Launch

After sourcing a PX4 ROS2 workspace that provides `px4_msgs`:

```bash
ros2 run uav_runtime_safety_monitor px4_environment_check --extra-setup /path/to/px4_ros2_ws/install/setup.bash --strict
ros2 launch uav_runtime_safety_monitor px4_safety_monitor.launch.py
```

This starts the PX4 telemetry bridge, safety monitor, and mission supervisor. It does not start PX4 SITL by itself.

To check live PX4 telemetry topics after PX4 SITL and the Micro XRCE-DDS Agent are running:

```bash
ros2 run uav_runtime_safety_monitor px4_environment_check --extra-setup /path/to/px4_ros2_ws/install/setup.bash --check-topics --strict
```

## Notes

The ROS2 package launch files and the `gazebo_extension/` demo scripts both run
the same packaged nodes through the typed message interfaces. There is a single
implementation of each node in `uav_runtime_safety_monitor/`; the earlier
`ros2_extension/` `std_msgs/String` JSON variant has been removed now that the
typed messages are the only interface.
