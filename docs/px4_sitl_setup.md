# PX4 SITL Setup Notes

This repository keeps PX4 as an optional integration layer. The Python, ROS2,
and Gazebo Classic demos remain the reliable fallback. PX4 SITL should be
installed in a separate workspace and connected through the `px4_state_bridge`
node.

## Why This Is Separate

The validated project environment uses ROS2 Foxy and Gazebo Classic. Current PX4
documentation targets newer PX4/Gazebo workflows for many setups, so the safest
approach is to isolate PX4 from this repository and only bridge telemetry into
the existing safety monitor.

Official references:

- PX4 ROS2 user guide: `https://docs.px4.io/main/en/ros2/user_guide.html`
- PX4 Gazebo simulation: `https://docs.px4.io/main/en/sim_gazebo_gz/`
- PX4 Ubuntu development environment: `https://docs.px4.io/main/en/dev_setup/dev_env_linux_ubuntu.html`

## Compatibility Rule

Do not mix ROS1 Noetic and ROS2 Foxy in the same terminal. If you previously
sourced Noetic, close the terminal and start a clean one.

Use this pattern when in doubt:

```bash
env -i HOME=$HOME USER=$USER LOGNAME=$LOGNAME PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin bash
```

Then source only the ROS2/PX4 environment needed for the test.

## Readiness Check

From the repository root:

```bash
python3 px4_extension/check_px4_environment.py
```

Expected before PX4 is installed:

- ROS2 Foxy should be found if `/opt/ros/foxy/setup.bash` exists.
- `px4_msgs` may be missing until a PX4 ROS2 workspace is built and sourced.
- `MicroXRCEAgent` may be missing until the PX4 ROS2/DDS bridge tools are
  installed.
- PX4 telemetry topics will be skipped unless `--check-topics` is used.

Strict mode is useful in scripts:

```bash
python3 px4_extension/check_px4_environment.py --strict
```

After PX4 SITL and DDS are running:

```bash
export PX4_ROS2_WS_SETUP=/path/to/px4_ros2_ws/install/setup.bash
python3 px4_extension/check_px4_environment.py --extra-setup "$PX4_ROS2_WS_SETUP" --check-topics --strict
```

## Runtime Stack

When the PX4 ROS2 workspace exists, run the monitor stack with:

```bash
cd /home/inteed/projects/uav-runtime-safety-monitor
export PX4_ROS2_WS_SETUP=/path/to/px4_ros2_ws/install/setup.bash
./px4_extension/run_px4_monitor_stack.sh
```

The helper script:

1. rejects mixed Noetic/Foxy shells,
2. sources ROS2 Foxy,
3. optionally sources the PX4 ROS2 workspace,
4. checks for `px4_msgs`,
5. builds this ROS2 package,
6. launches `px4_safety_monitor.launch.py`.

## PX4 Telemetry Acceptance Criteria

Before claiming live PX4 integration, verify:

```bash
ros2 topic list | grep /fmu/out/vehicle_local_position
ros2 topic list | grep /fmu/out/battery_status
ros2 topic echo /uav/state
ros2 topic echo /uav/safety_status
ros2 topic echo /uav/supervisor_mode
```

The minimum successful result is:

- PX4 publishes local position and battery telemetry.
- `px4_state_bridge` republishes that telemetry as `/uav/state`.
- `safety_monitor` publishes `/uav/safety_status`.
- `mission_supervisor` publishes `/uav/supervisor_mode`.

Command output back into PX4 should stay disabled until read-only telemetry has
been validated.
