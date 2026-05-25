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
safety_status_logger_node
```

## Planned Topics

```text
/uav/state
/uav/safety_status
/uav/recommended_action
/uav/safety_events
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

## Next Step

Create a minimal `rclpy` node that subscribes to simulated UAV state data and publishes a safety status string, severity, recommended action, and event transitions. After that, connect the same interface to PX4 SITL or Gazebo-generated state data.
