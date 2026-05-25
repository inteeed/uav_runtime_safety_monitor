# Runtime Safety Monitoring for Autonomous UAV Missions

## Overview

This project implements a small runtime safety-monitoring prototype for autonomous UAV missions. A simulated UAV follows waypoint-based missions while a safety monitor checks operational constraints such as altitude limits, geofence boundaries, battery level, mission timeout, and stale state updates. If a warning or violation is detected, the monitor logs the event and recommends a safe response such as warning, return-to-home, or landing.

The project is intended as preparation for UAV autonomy work involving ROS2, PX4/Gazebo simulation, log-data analysis, and safe operation of autonomous drones.

## Motivation

Autonomous UAVs need supervisory onboard software that can detect unsafe mission states during operation. This repository focuses on a narrow but relevant subsystem: a runtime monitor that receives UAV state data, checks safety constraints, produces a safety status and severity, and stores validation evidence from repeatable simulation scenarios.

## System Architecture

![System architecture](docs/architecture.png)

```text
Scenario Catalog
        |
        v
Mission Phase Planner
        |
        v
UAV State Data
        |
        v
Runtime Safety Monitor
        |
        v
Safety Status / Severity / Recommended Action
        |
        v
Simulation Runner
        |
        v
State Log + Event Log + Scenario Validation
        |
        v
Python Analysis and Plots
```

## Safety Rules

| Rule | Limit | Safety status | Severity | Recommended action |
| --- | --- | --- | --- | --- |
| Altitude warning | `z >= 25 m` and `z <= 30 m` | `ALTITUDE_WARNING` | `WARNING` | `WARNING` |
| Altitude limit | `z > 30 m` | `ALTITUDE_LIMIT_VIOLATION` | `CRITICAL` | `LAND` |
| Geofence warning | within `5 m` of boundary | `GEOFENCE_WARNING` | `WARNING` | `WARNING` |
| Geofence boundary | `x/y` outside `[-50, 50] m` | `GEOFENCE_VIOLATION` | `CRITICAL` | `RETURN_TO_HOME` |
| Low battery | `battery < 20%` | `LOW_BATTERY` | `CRITICAL` | `LAND` |
| Mission timeout | `time > 120 s` | `MISSION_TIMEOUT` | `CRITICAL` | `RETURN_TO_HOME` |
| State timeout | update gap `> 2 s` | `STATE_TIMEOUT` | `CRITICAL` | `RETURN_TO_HOME` |

The current safety limits are stored in [config/safety_limits.json](config/safety_limits.json).

## Implementation

The current version is intentionally lightweight and does not require PX4, Gazebo, or ROS2. It contains:

- [src/mission_simulator.py](src/mission_simulator.py): generates simulated UAV state samples for multiple validation scenarios.
- [src/scenario_catalog.py](src/scenario_catalog.py): defines scenarios, expected outcomes, and log names.
- [src/simulation_components.py](src/simulation_components.py): contains mission-phase planning and fault-injection components.
- [src/simulation_runner.py](src/simulation_runner.py): connects simulation, monitoring, state logs, and event logs.
- [src/safety_monitor.py](src/safety_monitor.py): evaluates safety rules, warning margins, stale updates, and priority between simultaneous conditions.
- [src/logger.py](src/logger.py): writes continuous state logs and event-transition logs.
- [src/main.py](src/main.py): runs all validation scenarios.
- [analysis/analyze_logs.py](analysis/analyze_logs.py): summarizes mission logs and event transitions.
- [analysis/plot_mission.py](analysis/plot_mission.py): creates validation plots.
- [analysis/validate_scenarios.py](analysis/validate_scenarios.py): checks each scenario against the expected monitor result.
- [tests/test_safety_monitor.py](tests/test_safety_monitor.py): unit tests for the monitor logic.

More detail is available in [docs/simulation_components.md](docs/simulation_components.md).

## Validation Scenarios

| Scenario | Injected condition | Expected status | Expected action |
| --- | --- | --- | --- |
| Normal mission | None | `SAFE` | `CONTINUE` |
| Geofence warning | UAV approaches boundary but remains inside | `GEOFENCE_WARNING` | `WARNING` |
| Geofence violation | UAV crosses `x = 50 m` boundary | `GEOFENCE_VIOLATION` | `RETURN_TO_HOME` |
| Altitude violation | UAV climbs above `30 m` | `ALTITUDE_LIMIT_VIOLATION` | `LAND` |
| Low battery | Battery drops below `20%` | `LOW_BATTERY` | `LAND` |
| Mission timeout | Mission time exceeds `120 s` | `MISSION_TIMEOUT` | `RETURN_TO_HOME` |
| State timeout | State update gap exceeds `2 s` | `STATE_TIMEOUT` | `RETURN_TO_HOME` |

## Results

The normal mission remains inside the geofence and below the altitude limit, so all samples are `SAFE`.

The geofence-violation mission first generates a warning near the boundary and then detects a critical `GEOFENCE_VIOLATION`, recommending `RETURN_TO_HOME`.

Generated figures:

![Geofence violation trajectory plot](results/geofence_violation_trajectory_plot.png)

![Geofence violation altitude plot](results/geofence_violation_altitude_plot.png)

![Geofence violation battery plot](results/geofence_violation_battery_plot.png)

![Geofence violation safety events plot](results/geofence_violation_safety_events_plot.png)

## How to Run

From the repository root:

```bash
python3 src/main.py
python3 analysis/validate_scenarios.py
python3 analysis/analyze_logs.py
python3 analysis/plot_mission.py
python3 analysis/create_architecture_diagram.py
python3 -m unittest discover
```

Expected generated files include:

```text
data/normal_mission.csv
data/normal_events.csv
data/geofence_warning_mission.csv
data/geofence_warning_events.csv
data/geofence_violation_mission.csv
data/geofence_violation_events.csv
data/altitude_violation_mission.csv
data/low_battery_mission.csv
data/timeout_mission.csv
data/state_timeout_mission.csv
results/geofence_violation_trajectory_plot.png
results/geofence_violation_altitude_plot.png
results/geofence_violation_battery_plot.png
results/geofence_violation_safety_events_plot.png
docs/architecture.png
```

## Environment Setup

Recommended local setup on a fresh machine:

```bash
git clone https://github.com/inteeed/uav_runtime_safety_monitor.git
cd uav_runtime_safety_monitor
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/main.py
```

This repository currently uses standard Python CSV handling and matplotlib plotting. The analysis code avoids pandas so that the first version remains easy to run in restricted environments.

## Relevance to UAV Autonomy

This project is designed as a small onboard autonomy component, not as a full drone simulator. It connects to safe UAV operation through:

- runtime monitoring of mission constraints,
- warning margins before critical violations,
- stale state-update detection,
- safety-status, severity, and recommended-action generation,
- event-based logging for log-data analysis,
- simulation-based validation scenarios,
- reusable simulation components with expected scenario outcomes,
- a path toward ROS2/PX4/Gazebo integration.

## Future Work

- Convert the safety monitor into a ROS2 `rclpy` node.
- Subscribe to `/uav/state` and publish `/uav/safety_status`, `/uav/recommended_action`, and `/uav/safety_events`.
- Add PX4 or ArduPilot SITL integration.
- Add Gazebo-based validation scenarios.
- Add position-deviation, velocity-limit, GPS-loss, and sensor-fault checks.
