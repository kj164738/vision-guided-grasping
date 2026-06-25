# Stage 3: Isaac Sim Scene and ROS2 Bridge

## Goal

Run the simulated RGB-D perception source and Panda joint command bridge:

```text
Isaac Sim on Windows
  publishes: /camera/image_raw
             /camera/depth/image_rect_raw
             /camera/color/camera_info
             /joint_states
             /tf
             /clock
  subscribes: /joint_command

WSL2 ROS2 Humble
  runs: yolo_world_ros
        localization
        sim_control panda_joint_demo_node
```

Official Isaac Sim ROS2 bridge docs:

https://docs.isaacsim.omniverse.nvidia.com/4.5.0/ros2_tutorials/index.html

## Scene

`sim/isaac/stage3_scene.py` creates:

- Franka Panda at `/panda`
- a simple table
- red, green, and blue cubes on the tabletop
- a fixed RGB-D camera at `/World/camera_color_optical_frame`
- ROS2 bridge OmniGraphs for camera, depth, camera info, TF, clock, joint states, and joint command subscription

The simulated camera uses `camera_color_optical_frame` as its frame id so stage 2 localization can transform detections into `base_link`.

## Windows Isaac Sim Setup

Install and launch Isaac Sim 4.5.0 on Windows. Before starting the script, make sure the ROS2 bridge extension is available.

Use the same ROS domain on Windows and WSL2:

```powershell
$env:ROS_DOMAIN_ID="30"
```

Run from an Isaac Sim Python environment. The exact executable path depends on your install location:

```powershell
cd C:\path\to\vision-guided-grasping
& "C:\path\to\isaac-sim\python.bat" sim\isaac\stage3_scene.py
```

Optional headless run:

```powershell
& "C:\path\to\isaac-sim\python.bat" sim\isaac\stage3_scene.py --headless
```

## WSL2 ROS2 Setup

Use the same domain:

```bash
export ROS_DOMAIN_ID=30
source /opt/ros/humble/setup.bash
cd ros2_ws
colcon build
source install/setup.bash
```

Check bridge topics:

```bash
ros2 topic list | grep -E 'camera|joint|tf|clock'
ros2 topic echo /joint_states --once
ros2 topic echo /camera/color/camera_info --once
```

In simulation mode, do not run `camera_source`; Isaac Sim publishes the camera topics.

## Joint Command Demo

Cycle through fixed Panda poses:

```bash
ros2 run sim_control panda_joint_demo_node \
  --ros-args \
  -p joint_command_topic:=/joint_command \
  -p preset:=cycle \
  -p publish_rate_hz:=10.0 \
  -p hold_seconds:=3.0
```

Publish one fixed pose:

```bash
ros2 run sim_control panda_joint_demo_node \
  --ros-args \
  -p preset:=observe_table
```

Available presets:

- `home`
- `observe_table`
- `pre_grasp_demo`
- `cycle`

## Pipeline Validation

Run the perception node against Isaac camera images:

```bash
ros2 run yolo_world_ros yolo_world_node \
  --ros-args \
  -p mock_detector:=true \
  -p text_prompt:=cube
```

Run localization:

```bash
ros2 run localization object_localizer_node \
  --ros-args \
  -p depth_topic:=/camera/depth/image_rect_raw \
  -p camera_info_topic:=/camera/color/camera_info \
  -p target_frame:=base_link
```

Inspect outputs:

```bash
ros2 topic echo /localized_objects --once
ros2 topic echo /debug/object_points --once
```

## Validation

Success criteria:

- Isaac Sim publishes RGB, depth, CameraInfo, TF, clock, and joint states.
- `panda_joint_demo_node` publishes `/joint_command`.
- Panda visibly changes pose in Isaac Sim.
- Stage 1 and stage 2 nodes can consume Isaac Sim camera data.

## Evidence Log

| Date | Command | Result | Notes |
| --- | --- | --- | --- |
| TBD | Isaac Sim scene startup | TBD | TBD |
| TBD | `ros2 topic list` | TBD | TBD |
| TBD | Panda joint demo | TBD | TBD |
| TBD | localization with Isaac data | TBD | TBD |
