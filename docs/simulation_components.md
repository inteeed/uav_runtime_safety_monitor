# Simulation Components

The Python simulation is organized as a small test harness rather than one monolithic script. This keeps the first version lightweight while making the structure closer to a ROS2/PX4/Gazebo validation setup.

## Components

| Component | File | Responsibility |
| --- | --- | --- |
| Scenario catalog | `src/scenario_catalog.py` | Defines mission scenarios, expected outcomes, and output log names. |
| Mission phase planner | `src/simulation_components.py` | Converts waypoints into takeoff, waypoint tracking, return-home, and landing segments. |
| Mission simulator | `src/mission_simulator.py` | Generates timestamped UAV state samples from mission segments, including planned reference positions. |
| Fault injector | `src/simulation_components.py` | Injects a state-update gap to emulate missing UAV state data. |
| Path-deviation injector | `src/mission_simulator.py` | Offsets the simulated UAV from its planned reference path for deviation-monitoring tests. |
| Runtime safety monitor | `src/safety_monitor.py` | Checks state samples against safety limits. |
| Mission supervisor | `src/mission_supervisor.py` | Converts monitor outputs into response modes such as warning, return-home, and landing. |
| Simulation runner | `src/simulation_runner.py` | Connects simulator, monitor, supervisor, state logging, and event logging. |
| Scenario validator | `analysis/validate_scenarios.py` | Runs every scenario and checks observed monitor output against expected results. |

## Why This Matters

This structure separates the simulation environment from the safety-monitoring logic. In a later ROS2/PX4/Gazebo version, the mission simulator can be replaced by real or simulated autopilot state data while keeping the monitor interface mostly unchanged.

```text
Python simulation:
Scenario Catalog -> Mission Simulator -> Runtime Safety Monitor -> Mission Supervisor -> Logs/Plots

ROS2/PX4 version:
PX4/Gazebo State Topic -> Runtime Safety Monitor Node -> Mission Supervisor Node -> Safety Action Topic
```

## Validation Command

Run:

```bash
python3 analysis/validate_scenarios.py
```

Expected result:

```text
10 / 10 scenarios passed
```

The validator checks both the monitor output and the supervisor response mode.
