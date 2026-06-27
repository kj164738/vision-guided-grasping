# Vision-Guided Grasping

Open-vocabulary perception scaffold for a ROS2 + YOLO-World visual grasping project.

The current implementation covers the first four milestones:

1. publish images from a local camera or video file;
2. run YOLO-World with a text prompt such as `cup,bottle,box`;
3. publish detections as `vision_msgs/Detection2DArray`;
4. convert detections plus aligned depth into 3D target points;
5. transform target points into `base_link` through TF2;
6. run an Isaac Sim scene that publishes simulated RGB-D data and accepts Panda joint commands;
7. execute a lightweight semantic grasp demo from `/localized_objects`.

Target runtime:

- WSL2 Ubuntu 22.04
- ROS2 Humble
- Python 3.10
- Official YOLO-World repository and checkpoints

The current Windows workspace is only used to author the project. Build and runtime commands should be executed inside WSL2/Ubuntu.

## Repository Layout

```text
vision-guided-grasping/
+-- ros2_ws/
|   +-- src/
|       +-- camera_source/
|       +-- grasp_execution/
|       +-- localization/
|       +-- sim_control/
|       +-- yolo_world_ros/
+-- docs/
|   +-- stage1_perception.md
|   +-- stage2_localization.md
|   +-- stage3_isaac_sim.md
|   +-- stage4_grasp_execution.md
+-- sim/
|   +-- isaac/
|       +-- stage3_scene.py
+-- scripts/
```

## ROS2 Interfaces

`camera_source` publishes:

- `/camera/image_raw` (`sensor_msgs/msg/Image`)

`yolo_world_ros` subscribes:

- `/camera/image_raw` (`sensor_msgs/msg/Image`)

`yolo_world_ros` publishes:

- `/detections` (`vision_msgs/msg/Detection2DArray`)
- `/debug/detection_image` (`sensor_msgs/msg/Image`)

`localization` subscribes:

- `/detections` (`vision_msgs/msg/Detection2DArray`)
- `/camera/depth/image_rect_raw` (`sensor_msgs/msg/Image`)
- `/camera/color/camera_info` (`sensor_msgs/msg/CameraInfo`)
- TF from `camera_color_optical_frame` to `base_link`

`localization` publishes:

- `/localized_objects` (`vision_msgs/msg/Detection3DArray`)
- `/debug/object_points` (`geometry_msgs/msg/PoseArray`)

Isaac Sim publishes in simulation mode:

- `/camera/image_raw` (`sensor_msgs/msg/Image`)
- `/camera/depth/image_rect_raw` (`sensor_msgs/msg/Image`)
- `/camera/color/camera_info` (`sensor_msgs/msg/CameraInfo`)
- `/joint_states` (`sensor_msgs/msg/JointState`)
- `/tf` (`tf2_msgs/msg/TFMessage`)
- `/clock` (`rosgraph_msgs/msg/Clock`)

Isaac Sim subscribes:

- `/joint_command` (`sensor_msgs/msg/JointState`)

`sim_control` publishes:

- `/joint_command` (`sensor_msgs/msg/JointState`)

`grasp_execution` subscribes:

- `/localized_objects` (`vision_msgs/msg/Detection3DArray`)

`grasp_execution` publishes:

- `/joint_command` (`sensor_msgs/msg/JointState`)
- `/grasp/status` (`std_msgs/msg/String`)

Core `yolo_world_ros` parameters:

- `text_prompt`: comma-separated text classes, for example `cup,bottle,box`
- `confidence_threshold`: minimum score for detections
- `device`: `cuda:0` or `cpu`
- `model_config`: YOLO-World config file path
- `checkpoint_path`: YOLO-World checkpoint path
- `mock_detector`: set `true` for ROS topic debugging without model files

Core `localization` parameters:

- `target_frame`: output frame, default `base_link`
- `depth_window_size`: median depth window size around the bbox center
- `min_depth_m` and `max_depth_m`: valid localization depth range
- `sync_tolerance_sec`: max allowed timestamp difference between detections and depth

Core `sim_control` parameters:

- `preset`: `cycle`, `home`, `observe_table`, or `pre_grasp_demo`
- `joint_command_topic`: default `/joint_command`
- `publish_rate_hz`: default `10.0`
- `hold_seconds`: seconds to hold each preset when cycling

Core `grasp_execution` parameters:

- `target_label`: semantic target label, or empty for the first localized object
- `auto_start`: start the grasp demo as soon as a matching target arrives
- `state_hold_seconds`: seconds to hold each demo state
- `joint_command_topic`: default `/joint_command`

## WSL2 Setup

Install ROS2 Humble and common dependencies in Ubuntu 22.04:

```bash
sudo apt update
sudo apt install -y \
  ros-humble-desktop \
  ros-humble-cv-bridge \
  ros-humble-vision-msgs \
  ros-humble-tf2-ros \
  ros-humble-tf2-msgs \
  ros-humble-std-msgs \
  python3-colcon-common-extensions \
  python3-pip
```

Source ROS2:

```bash
source /opt/ros/humble/setup.bash
```

Install Python dependencies used by the ROS nodes:

```bash
python3 -m pip install opencv-python numpy pytest
```

Install YOLO-World separately from the official repository:

```bash
git clone --recursive https://github.com/AILab-CVC/YOLO-World.git ~/YOLO-World
cd ~/YOLO-World
python3 -m pip install -e .
```

Download a YOLO-World config and checkpoint following the model card in the official repository, then pass those paths to the ROS node.

## Build

From this repository root inside WSL2:

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

## Run With Mock Detector

Use this first to verify the ROS2 topic loop without model files:

```bash
ros2 run camera_source camera_source_node \
  --ros-args \
  -p source_type:=camera \
  -p camera_index:=0
```

In another terminal:

```bash
ros2 run yolo_world_ros yolo_world_node \
  --ros-args \
  -p mock_detector:=true \
  -p text_prompt:=cup,bottle,box
```

Inspect topics:

```bash
ros2 topic list
ros2 topic echo /detections --once
rqt_image_view /debug/detection_image
```

## Run Stage 2 Localization

Stage 2 expects aligned RGB-D data and camera intrinsics. For early testing, publish a static transform:

```bash
ros2 run tf2_ros static_transform_publisher \
  0 0 0 0 0 0 \
  base_link camera_color_optical_frame
```

Run the localizer:

```bash
ros2 run localization object_localizer_node \
  --ros-args \
  -p detections_topic:=/detections \
  -p depth_topic:=/camera/depth/image_rect_raw \
  -p camera_info_topic:=/camera/color/camera_info \
  -p target_frame:=base_link \
  -p depth_window_size:=5 \
  -p min_depth_m:=0.05 \
  -p max_depth_m:=3.0
```

Inspect localized targets:

```bash
ros2 topic echo /localized_objects --once
ros2 topic echo /debug/object_points --once
```

## Run Stage 3 Isaac Sim Bridge

Stage 3 uses Isaac Sim as the camera source. Do not run `camera_source` while the Isaac scene is publishing camera topics.

Use the same ROS domain in Windows and WSL2. Example:

PowerShell:

```powershell
$env:ROS_DOMAIN_ID="30"
```

WSL2:

```bash
export ROS_DOMAIN_ID=30
```

Start the Isaac Sim scene from an Isaac Sim Python environment on Windows:

```powershell
cd C:\path\to\vision-guided-grasping
& "C:\path\to\isaac-sim\python.bat" sim\isaac\stage3_scene.py
```

In WSL2, build and inspect bridge topics:

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
ros2 topic list | grep -E 'camera|joint|tf|clock'
```

Drive the Panda through fixed joint presets:

```bash
ros2 run sim_control panda_joint_demo_node \
  --ros-args \
  -p joint_command_topic:=/joint_command \
  -p preset:=cycle \
  -p publish_rate_hz:=10.0 \
  -p hold_seconds:=3.0
```

## Run Stage 4 Grasp Execution

Run after Isaac Sim, perception, and localization are publishing `/localized_objects`:

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

## Run With YOLO-World

```bash
ros2 run yolo_world_ros yolo_world_node \
  --ros-args \
  -p text_prompt:=cup,bottle,box \
  -p confidence_threshold:=0.2 \
  -p device:=cuda:0 \
  -p model_config:=/home/$USER/YOLO-World/configs/pretrain/<config>.py \
  -p checkpoint_path:=/home/$USER/YOLO-World/weights/<checkpoint>.pth
```

If the config, checkpoint, or YOLO-World dependencies are missing, the node logs a clear startup error and exits instead of silently publishing empty detections.

## Local Non-ROS Checks

The pure Python tests avoid ROS2 and model dependencies:

```bash
cd ros2_ws/src/yolo_world_ros
python3 -m pytest
cd ../localization
python3 -m pytest
cd ../sim_control
python3 -m pytest
cd ../grasp_execution
python3 -m pytest
```

## Completed Stages

- Stage 1: ROS2 image ingestion, YOLO-World wrapper, 2D detections, and debug image output.
- Stage 2: RGB-D center-point localization, CameraInfo projection, TF transform into `base_link`, and 3D detection output.
- Stage 3: Isaac Sim scene scaffold, ROS2 bridge topic design, simulated RGB-D source, TF, joint states, and Panda joint command demo.
- Stage 4: Lightweight semantic grasp state machine that consumes `/localized_objects` and publishes `/joint_command`.

## Unfinished Work

The current grasp execution is a lightweight demo. The production version still needs:

- IK from object pose to joint-space goals;
- MoveIt2 or another planner for collision-aware motion;
- a real gripper command topic and grasp closure handling;
- object attachment or physics-based pickup validation;
- robust timeout, recovery, and retry policies.

Stage 5 can add a small Sim2Real robustness experiment:

- randomize Isaac Sim lighting, object color/material, table texture, camera pose, and background;
- record YOLO-World detection confidence and localization stability across randomized scenes;
- summarize failure cases and practical transfer limits in `docs/`.

Validation still required on the target runtime:

- run `colcon build` in WSL2 Ubuntu 22.04 with ROS2 Humble;
- run the Isaac Sim 4.5 scene on Windows and confirm all bridge topics are visible from WSL2;
- verify Panda responds to `/joint_command`;
- run the full stage 1 to stage 3 pipeline with Isaac camera data.
