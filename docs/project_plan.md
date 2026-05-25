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
- low-battery check
- mission-timeout check
- warning margins
- stale state-update detection
- status severity and recommended action
- event-transition logs
- unit tests

Status: in progress.

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

## Phase 4: Documentation

Deliverables:

- README
- safety requirements
- architecture diagram
- results images
- validation matrix

Status: in progress.

## Phase 5: ROS2/PX4 Extension

Deliverables:

- ROS2 node skeleton
- `/uav/state` subscriber
- `/uav/safety_status` publisher
- `/uav/recommended_action` publisher
- `/uav/safety_events` publisher
- future PX4/Gazebo integration notes

Status: planned.
