# Stage 4: Lightweight Grasp Execution

## Goal

Run a simple semantic grasp demo without MoveIt2:

```text
/localized_objects
        |
        v
simple_grasp_executor_node
        |
        +--> /joint_command
        +--> /grasp/status
```

This stage turns localized 3D detections into a fixed Panda joint-command sequence for Isaac Sim. It demonstrates the system-level grasp pipeline without inverse kinematics, collision checking, gripper physics, or true object pickup.

## Interfaces

Inputs:

- `/localized_objects` (`vision_msgs/msg/Detection3DArray`)

Outputs:

- `/joint_command` (`sensor_msgs/msg/JointState`)
- `/grasp/status` (`std_msgs/msg/String`)

## Behavior

The node selects a target and executes one grasp demo:

```text
idle -> approach -> descend -> close_gripper -> lift -> retreat -> done
```

Target selection:

- `target_label:=""` selects the first localized object.
- `target_label:="cube"` selects the first object whose class id is `cube`.
- no detection or no matching label keeps the node idle.

The 3D target point is logged and preserved as the semantic target for later stages. Joint angles come from fixed demo presets.

## Run

Build in WSL2 Ubuntu 22.04:

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

Run after Isaac Sim, perception, and localization are publishing:

```bash
ros2 run grasp_execution simple_grasp_executor_node \
  --ros-args \
  -p localized_objects_topic:=/localized_objects \
  -p joint_command_topic:=/joint_command \
  -p status_topic:=/grasp/status \
  -p target_label:=cube \
  -p auto_start:=true
```

Inspect progress:

```bash
ros2 topic echo /grasp/status
ros2 topic echo /joint_command --once
```

## Validation

Success criteria:

- `/grasp/status` reports target acquisition and state transitions.
- `/joint_command` publishes Panda joint names `panda_joint1` through `panda_joint7`.
- Panda visibly moves through approach, descend, lift, and retreat demo poses in Isaac Sim.

## Limits

This stage intentionally does not implement:

- IK from object pose to joint angles
- MoveIt2 planning
- collision checking
- physical gripper closure
- real object attachment or pickup

Those are the next engineering steps after the lightweight demo is verified.
