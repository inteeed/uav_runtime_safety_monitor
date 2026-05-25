# ROS2 Extension

This folder keeps the original script-based ROS2 mapping. The recommended ROS2 interface is now the `ament_python` package in the repository root; see [docs/ros2_package.md](../docs/ros2_package.md).

The script extension remains useful as a simple fallback and for inspecting the node logic without building the package.

The first ROS2 version uses `std_msgs/String` with JSON payloads. This avoids custom message-generation setup while still showing the node/topic architecture. A later version can replace these JSON strings with custom UAV state and safety-status messages.

## Nodes

```text
uav_state_publisher_node
        |
        v
safety_monitor_node
        |
        v
mission_supervisor_node
```

Implemented scripts:

- `uav_state_publisher_node.py`
- `safety_monitor_node.py`
- `mission_supervisor_node.py`
- `ros2_json.py`

## Topics

```text
/uav/state
/uav/safety_status
/uav/recommended_action
/uav/supervisor_mode
```

## State JSON Fields

```text
time_s
frame_id
x_m
y_m
z_m
vx_mps
vy_mps
vz_mps
battery_percent
mission_state
```

## Safety Status JSON Fields

```text
safety_status
severity
recommended_action
detail
```

## Supervisor JSON Fields

```text
supervisor_mode
active_response
response_reason
response_started
```

## How to Run

Recommended package launch:

```bash
source /opt/ros/foxy/setup.bash
colcon build --symlink-install --packages-select uav_runtime_safety_monitor
source install/setup.bash
ros2 launch uav_runtime_safety_monitor gazebo_safety_demo.launch.py
```

Script fallback:

Use a terminal with ROS2 sourced. For Foxy:

```bash
source /opt/ros/foxy/setup.bash
cd /home/inteed/projects/uav-runtime-safety-monitor
```

Use a clean terminal for ROS2. Do not source ROS Noetic and ROS2 Foxy in the same shell.

Terminal 1:

```bash
python3 ros2_extension/safety_monitor_node.py
```

Terminal 2:

```bash
python3 ros2_extension/mission_supervisor_node.py
```

Terminal 3:

```bash
python3 ros2_extension/uav_state_publisher_node.py
```

Optional topic inspection:

```bash
ros2 topic echo /uav/state
ros2 topic echo /uav/safety_status
ros2 topic echo /uav/supervisor_mode
```

## Limitations

The script-based version uses JSON over `std_msgs/String`. A later package version can replace these payloads with custom ROS2 messages.
