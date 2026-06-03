# PX4 Closed-Loop Validation Runbook

This runbook flies PX4 SITL *past the real geofence*, lets the monitor detect the
breach from genuine telemetry, and lets the supervisor command a real
return-to-launch through the guarded command bridge. It produces evidence that
the loop closed end to end — not an injected fault.

> SITL / test-stand use only. The command bridge actually moves the vehicle.

## Prerequisites

- PX4 Gazebo Classic SITL set up (see [px4_sitl_setup.md](px4_sitl_setup.md)).
- A PX4 ROS2 workspace providing `px4_msgs`. Export its setup before running:
  `export PX4_ROS2_WS_SETUP=/path/to/px4_ros2_ws/install/setup.bash`
- The Micro XRCE-DDS Agent installed.

## Terminals

Run each block in its own terminal from the repository root.

```bash
# Terminal 1 — PX4 Gazebo Classic SITL
HEADLESS=0 ./px4_extension/run_px4_gazebo_classic.sh
```

At the PX4 `pxh>` prompt, take off so the vehicle is airborne before offboard:

```bash
commander takeoff
```

```bash
# Terminal 2 — Micro XRCE-DDS Agent (PX4 <-> ROS2 bridge)
./px4_extension/run_micro_xrce_agent.sh
```

```bash
# Terminal 3 — monitor stack WITH the closed-loop command bridge enabled
./px4_extension/run_px4_monitor_stack.sh enable_command_bridge:=true
```

Wait until the safety console prints `SAFE` and the bridge logs
`PX4 command bridge ARMED`.

```bash
# Terminal 4 — fly the vehicle past the geofence (real telemetry breach)
./px4_extension/trigger_real_geofence_flight.sh
```

## What should happen

1. The vehicle flies outbound toward `x = 60 m` (geofence `x_max` is `50 m`).
2. The monitor reports `GEOFENCE_VIOLATION` from real telemetry and recommends
   `RETURN_TO_HOME`.
3. The supervisor switches to `RETURNING_HOME`; the command bridge logs
   `Sent PX4 command 20` (RTL).
4. `trigger_real_geofence_flight.sh` sees the supervisor response and releases
   offboard control, so PX4 executes the return.

If PX4 does not auto-engage RTL when offboard is released, command it manually in
Terminal 1 to confirm the rest of the chain: `commander mode auto:rtl`. (Getting
the failsafe/mode transition to engage automatically is the main thing to verify
on a real run.)

## Capture and validate the evidence

```bash
# Confirm: real flown breach + supervisor response + a VehicleCommand was sent
python3 analysis/validate_closed_loop.py \
  --require-real-telemetry \
  --command-log data/px4_command_log.csv

# Regenerate the live plots
python3 analysis/analyze_logs.py data/px4_live_mission.csv
python3 analysis/plot_mission.py --input data/px4_live_mission.csv --prefix px4_live
```

What each check proves:

- `--require-real-telemetry`: the violating sample's `frame_id` is
  `px4_local_ned_converted`, not `..._fault_injected` — the breach was genuinely
  flown, not injected.
- `--command-log`: the command bridge actually issued an RTL/Land
  `VehicleCommand` (recorded in `data/px4_command_log.csv`).

These confirm the decision chain ran and a command was *sent*. That PX4
*accepted* the command and returned is confirmed visually from the `px4_live`
trajectory plot (outbound, then back toward home). Update the README
"PX4/Gazebo Live Telemetry Evidence" section with the new event log and plot.
