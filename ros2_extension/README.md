# ROS2 Extension

The current project is a pure Python prototype with a lightweight ROS2 mapping. The ROS2 extension keeps the same safety-monitoring and supervisor logic and wraps it as onboard-style ROS2 components.

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
        |
        v
safety_status_logger_node
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
/uav/safety_events
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
```

## How to Run

Use a terminal with ROS2 sourced. For Foxy:

```bash
source /opt/ros/foxy/setup.bash
cd /home/inteed/projects/uav-runtime-safety-monitor
```

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

This is not a full ROS2 package yet. It is a script-based extension that demonstrates how the Python safety monitor maps to ROS2 publishers and subscribers. The next step would be a proper `ament_python` package with launch files and custom messages.
