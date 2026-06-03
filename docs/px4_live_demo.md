# PX4 Gazebo Live Monitor Demo

This demo connects PX4 Gazebo Classic telemetry to the project safety monitor.
It is read-only with respect to PX4: the monitor observes telemetry, logs safety
status, and publishes supervisor mode inside ROS2, but it does not command PX4.

Use separate terminals.

## Terminal 1: PX4 Gazebo Classic

```bash
HEADLESS=0 /bin/bash /home/inteed/projects/uav-runtime-safety-monitor/px4_extension/run_px4_gazebo_classic.sh
```

When the `pxh>` prompt appears and PX4 reports `Ready for takeoff`, run:

```bash
commander takeoff
```

The drone should take off and hold position in Gazebo.

## Terminal 2: Micro XRCE-DDS Agent

```bash
/bin/bash /home/inteed/projects/uav-runtime-safety-monitor/px4_extension/run_micro_xrce_agent.sh
```

Expected result: the agent reports a PX4 client session, and PX4 reports
`uxrce_dds_client` topic creation.

## Terminal 3: Safety Monitor Stack

```bash
export PX4_ROS2_WS_SETUP=/home/inteed/projects/px4_ros2_ws/install/setup.bash
/bin/bash /home/inteed/projects/uav-runtime-safety-monitor/px4_extension/run_px4_monitor_stack.sh
```

Expected result:

```text
PX4 bridge ready: /fmu/out/vehicle_local_position + /fmu/out/battery_status -> /uav/raw_state
Fault injector ready: /uav/raw_state -> /uav/state
Safety monitor node ready
Mission supervisor node ready
Safety console ready
Live mission log: .../data/px4_live_mission.csv
Live event log: .../data/px4_live_events.csv
[INFO] status=SAFE action=CONTINUE ...
```

The readable safety output is printed in this terminal. The typed `/uav/state`
topic is useful for debugging, but the safety console is the better view for a
demo.

## Terminal 4: Trigger A Monitor Violation

For a guaranteed monitor test, request a short fault injection on the PX4
telemetry stream:

```bash
/bin/bash /home/inteed/projects/uav-runtime-safety-monitor/px4_extension/inject_monitor_violation.sh geofence
```

Expected monitor output in Terminal 3:

```text
[CRITICAL] status=GEOFENCE_VIOLATION action=RETURN_TO_HOME ... supervisor=RETURNING_HOME response=RETURN_TO_HOME ...
```

Other supported injected scenarios:

```bash
/bin/bash /home/inteed/projects/uav-runtime-safety-monitor/px4_extension/inject_monitor_violation.sh altitude
/bin/bash /home/inteed/projects/uav-runtime-safety-monitor/px4_extension/inject_monitor_violation.sh battery
```

To disturb the Gazebo model itself, use:

```bash
/bin/bash /home/inteed/projects/uav-runtime-safety-monitor/px4_extension/trigger_gazebo_geofence_violation.sh
/bin/bash /home/inteed/projects/uav-runtime-safety-monitor/px4_extension/trigger_gazebo_altitude_violation.sh
```

Gazebo disturbances are less deterministic because PX4 may reject or quickly
correct the pose disturbance. They are useful for visual testing; the telemetry
fault injection is the reliable safety-monitor validation.

The fault-injection path keeps one monitor input stream:

```text
PX4 telemetry -> /uav/raw_state -> fault injector -> /uav/state -> safety monitor
```

This avoids mixing PX4 and synthetic timestamps in the monitor input.

## Analyze The Live Log

After the monitor stack has run for a few seconds:

```bash
cd /home/inteed/projects/uav-runtime-safety-monitor
python3 analysis/analyze_logs.py data/px4_live_mission.csv
python3 analysis/plot_mission.py --input data/px4_live_mission.csv --prefix px4_live
cat data/px4_live_events.csv
```

Expected generated plots:

```text
results/px4_live_trajectory_plot.png
results/px4_live_altitude_plot.png
results/px4_live_battery_plot.png
results/px4_live_safety_events_plot.png
results/px4_live_supervisor_response_plot.png
```

## Notes

Do not mix ROS Noetic and ROS2 Foxy in the same terminal. The helper scripts
restart in a clean environment when possible, but a fresh terminal is still the
least error-prone option.

Repeated PX4 messages such as `simulator_mavlink poll timeout` can appear while
the simulator continues to run. Treat the Gazebo view, `/fmu/out` ROS2 topics,
`/uav/state`, and the safety console output as the acceptance signals.
