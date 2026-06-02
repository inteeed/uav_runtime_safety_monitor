# Project Plan

## Goal

Build a small runtime safety-monitoring prototype for autonomous UAV missions. The project should remain simple and runnable while representing a believable onboard safety-supervisor component.

## Phase 1: Basic Python Simulation

Deliverables:

- waypoint-based mission simulator
- normal mission scenario
- unsafe geofence scenario
- CSV output

Status: complete.

## Phase 2: Runtime Safety Monitoring

Deliverables:

- altitude-limit check
- geofence check
- velocity-limit check
- planned-path deviation check
- low-battery check
- mission-timeout check
- warning margins
- stale state-update detection
- status severity and recommended action
- event-transition logs
- unit tests

Status: complete.

## Phase 3: Log Analysis

Deliverables:

- mission summary script
- event-transition summary
- scenario catalog with expected monitor outcomes
- reusable simulation runner
- mission phase planner
- basic fault injector for missing state updates
- automated scenario validation command
- trajectory plot with geofence boundary
- altitude plot
- battery plot
- safety-status plot

Status: complete for Python logs and reusable simulation components, expandable for ROS2/PX4 logs later.

## Phase 4: Safety Supervisor Response Simulation

Deliverables:

- mission supervisor component
- warning, return-home, and landing response modes
- response-aware CSV logs
- supervisor-response plots
- scenario validation of monitor output and supervisor response

Status: complete.

## Phase 5: Documentation and Application Polish

Deliverables:

- README
- safety requirements
- architecture diagram
- results images
- validation matrix

Status: complete.

## Phase 6: ROS2 and Gazebo Script Extension

Deliverables:

- script-based ROS2 state publisher
- script-based safety monitor node
- script-based mission supervisor node
- Gazebo Classic world
- Gazebo UAV model
- Gazebo model-state bridge
- Gazebo mission commander
- headless and GUI demo scripts

Status: complete.

## Phase 7: Gazebo Integration Validation

Deliverables:

- automated Gazebo demo log validation
- expected monitor/supervisor response checks
- unique Gazebo master URI per demo run
- tests for log-validation behavior

Status: complete.

## Phase 8: ROS2 Package and Launch Files

Deliverables:

- `ament_python` package metadata
- ROS2 console entry points
- visible Gazebo launch file
- headless Gazebo launch file
- installed Gazebo model, world, and safety config
- reduced ROS2 log noise
- more detailed quadrotor-style Gazebo UAV model

Status: complete.

## Phase 9: PX4 SITL Extension

Deliverables:

- PX4 integration plan
- state-bridge design from PX4 telemetry to `/uav/state`
- `px4_state_bridge` ROS2 node
- `px4_safety_monitor.launch.py`
- tests for PX4 NED-to-monitor-state mapping
- PX4 Gazebo Classic SITL telemetry smoke test

Status: complete for bridge scaffold and live telemetry smoke validation.

## Phase 10: PX4 Readiness Workflow

Deliverables:

- preflight checker for ROS2/PX4 environment readiness
- mixed Noetic/Foxy shell detection
- `px4_msgs` availability check
- Micro XRCE-DDS Agent availability check
- optional live PX4 telemetry topic check
- helper script for launching the monitor stack after PX4 workspace setup
- PX4 SITL setup notes and acceptance criteria
- live fault-injection workflow for readable monitor validation
- PX4 live telemetry CSV logs and plots

Status: complete for project-side readiness checks and one live PX4/Gazebo telemetry validation run.

## Phase 11: Expanded Safety Scenarios

Deliverables:

- velocity-limit scenario
- planned-path deviation scenario
- planned reference fields in mission logs
- plots that overlay actual trajectory and planned reference trajectory
- validation cases for the new monitor outcomes

Status: complete for deterministic Python simulation; richer cross-track/along-track trajectory checks remain future work.
