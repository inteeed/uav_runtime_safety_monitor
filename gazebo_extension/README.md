# Gazebo Simulation Extension

This extension runs the runtime safety monitor against a Gazebo Classic
simulation. The recommended package launch bridges Gazebo model state into the
typed `/uav/state` ROS2 topic. The script fallback in this folder still uses the
older JSON-over-`std_msgs/String` path for simple log-validation runs.

This is not PX4 SITL yet. It is a Gazebo-based integration step that demonstrates:

- a real Gazebo world and UAV model,
- Gazebo model state converted into the project's UAV state interface,
- runtime safety monitoring from Gazebo state,
- mission-supervisor response feedback into the Gazebo commander.

## Components

| Component | File | Purpose |
| --- | --- | --- |
| Gazebo world | `worlds/uav_safety_demo.world` | Loads the UAV model, geofence marker, Gazebo ROS state plugin, ground plane, and sun. |
| UAV model | `models/safety_uav/model.sdf` | Lightweight quadrotor-style UAV with arms, rotors, landing skids, sensor payload, and navigation markers. |
| Gazebo state bridge | `gazebo_state_bridge_node.py` | Subscribes to `/model_states` and publishes `/uav/state`. |
| Gazebo mission commander | `gazebo_mission_commander_node.py` | Moves the UAV model through a scenario and reacts to `/uav/supervisor_mode`. |
| Headless demo runner | `run_headless_demo.sh` | Starts Gazebo server and all ROS2 bridge/monitor/supervisor/commander scripts for one smoke test. |
| GUI demo runner | `run_gui_demo.sh` | Starts the visible Gazebo GUI and runs the same ROS2 bridge/monitor/supervisor/commander pipeline. |

## Visible Gazebo Demo

Recommended ROS2 package launch:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
colcon build --symlink-install --base-paths . interfaces/uav_runtime_safety_monitor_msgs --packages-up-to uav_runtime_safety_monitor
source install/setup.bash
ros2 launch uav_runtime_safety_monitor gazebo_safety_demo.launch.py
```

Use this when you want to see the Gazebo window:

```bash
cd /home/inteed/projects/uav-runtime-safety-monitor
./gazebo_extension/run_gui_demo.sh
```

The default scenario is `geofence_violation`. The UAV marker should move toward the geofence, cross the boundary, then return home and land after the supervisor response is triggered.

Important: run this from a clean terminal. Do not source ROS Noetic first. The script sources ROS2 Foxy itself.

## One-Command Headless Test

Recommended ROS2 package launch:

```bash
ros2 launch uav_runtime_safety_monitor gazebo_headless_safety_demo.launch.py
```

Use this first if you only want to verify that Gazebo and ROS2 are connected:

```bash
cd /home/inteed/projects/uav-runtime-safety-monitor
./gazebo_extension/run_headless_demo.sh
```

The default scenario is `geofence_violation`. You can run another scenario like this:

```bash
./gazebo_extension/run_headless_demo.sh altitude_violation
```

The script writes logs under `results/gazebo_demo_logs/` and prints a short summary showing the monitor status, supervisor mode, and inserted response commands.
It also calls `analysis/validate_gazebo_logs.py` and exits with a failure if the expected safety-monitor/supervisor response is missing.
Each run uses a unique `GAZEBO_MASTER_URI` so it does not attach to an unrelated Gazebo session already running on the default port.

## Manual GUI Run

Use clean terminals with ROS2 Foxy sourced. Do not source Noetic and Foxy in the same terminal.

In every terminal:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
cd /home/inteed/projects/uav-runtime-safety-monitor
export GAZEBO_MODEL_PATH=$PWD/gazebo_extension/models:$GAZEBO_MODEL_PATH
```

Terminal 1, start Gazebo:

```bash
gazebo --verbose gazebo_extension/worlds/uav_safety_demo.world
```

If Gazebo GUI is not available, use the headless server instead:

```bash
gzserver --verbose gazebo_extension/worlds/uav_safety_demo.world
```

Build and source the workspace once (the typed messages require a colcon
build), then run the packaged nodes:

```bash
colcon build --symlink-install --base-paths . interfaces/uav_runtime_safety_monitor_msgs --packages-up-to uav_runtime_safety_monitor
source install/setup.bash
```

Terminal 2, bridge Gazebo model state to `/uav/state`:

```bash
ros2 run uav_runtime_safety_monitor gazebo_state_bridge
```

Terminal 3, run the safety monitor:

```bash
ros2 run uav_runtime_safety_monitor safety_monitor
```

Terminal 4, run the mission supervisor:

```bash
ros2 run uav_runtime_safety_monitor mission_supervisor
```

Terminal 5, command the Gazebo UAV through an unsafe mission:

```bash
ros2 run uav_runtime_safety_monitor gazebo_mission_commander
```

The `run_headless_demo.sh` / `run_gui_demo.sh` scripts automate exactly this.

Expected behavior:

```text
GEOFENCE_WARNING
GEOFENCE_VIOLATION
RETURN_TO_HOME
RETURNING_HOME
```

The Gazebo commander inserts a return-home response after the supervisor publishes `RETURNING_HOME`.

## Useful Topic Checks

```bash
ros2 topic list
ros2 topic echo /model_states
ros2 topic echo /uav/state
ros2 topic echo /uav/safety_status
ros2 topic echo /uav/supervisor_mode
```

## Validate Existing Logs

After a demo run, validate its log directory directly:

```bash
python3 analysis/validate_gazebo_logs.py results/gazebo_demo_logs/<run_id> --scenario geofence_violation
```

A passing validation prints:

```text
Gazebo integration validation: PASS
```

## Other Scenarios

```bash
python3 gazebo_extension/gazebo_mission_commander_node.py --ros-args -p scenario:=altitude_violation
python3 gazebo_extension/gazebo_mission_commander_node.py --ros-args -p scenario:=low_battery
python3 gazebo_extension/gazebo_mission_commander_node.py --ros-args -p scenario:=mission_timeout
```

## Limitations

- This is a kinematic Gazebo simulation: the commander sets model state directly through Gazebo's `/set_entity_state` service.
- It does not use PX4, ArduPilot, or motor/flight dynamics yet.
- The purpose is to validate the runtime safety-monitoring pipeline against Gazebo-originated state data before moving to PX4/Gazebo SITL.
- Gazebo Classic is used for compatibility with the available ROS2 Foxy/Gazebo setup. A later version can migrate the world to modern Gazebo.
