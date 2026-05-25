# ROS2 Extension Plan

The current project is a pure Python prototype. The planned ROS2 extension will keep the same safety-monitoring logic and wrap it as an onboard software component.

## Planned Nodes

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

## Planned Topics

```text
/uav/state
/uav/safety_status
/uav/recommended_action
/uav/safety_events
/uav/supervisor_mode
```

## Planned State Message Fields

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

## Planned Safety Status Fields

```text
safety_status
severity
recommended_action
detail
```

## Planned Supervisor Fields

```text
supervisor_mode
active_response
response_reason
```

## Next Step

Create a minimal `rclpy` safety-monitor node and a small mission-supervisor node. The monitor publishes safety status, severity, and recommended action; the supervisor consumes those outputs and publishes a high-level response mode such as `RETURNING_HOME` or `LANDING`. After that, connect the same interface to PX4 SITL or Gazebo-generated state data.
