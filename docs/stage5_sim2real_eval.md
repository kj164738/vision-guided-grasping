# Stage 5: Sim2Real Randomization Evaluation

This stage adds a lightweight robustness experiment around the completed simulation pipeline. It does not claim full real transfer. The goal is to show that the project can define repeatable domain-randomized trials, run perception/localization under varied conditions, and summarize the observed failure modes.

## Scope

Implemented:

- deterministic trial generation for light intensity, table color, object color, and camera perturbation;
- randomized Isaac Sim scene entrypoint;
- CSV result schema for manual or scripted result recording;
- metrics for target detection rate, localization success rate, mean confidence, and 3D point stability;
- Markdown report generation.

Not implemented:

- real robot data collection;
- automatic rosbag parsing;
- real-domain versus sim-domain comparison;
- physics-based grasp success measurement.

## Generate Trials

From WSL2 after building and sourcing the ROS2 workspace:

```bash
ros2 run sim2real_eval generate_trials -- \
  --count 10 \
  --seed 42 \
  --target-label cube \
  --output outputs/sim2real_trials.csv
```

The generated CSV uses this schema:

```text
trial_id,seed,light_intensity,table_color_r,table_color_g,table_color_b,
object_color_r,object_color_g,object_color_b,camera_x,camera_y,camera_z,
camera_roll,camera_pitch,camera_yaw,target_label
```

## Run a Randomized Isaac Scene

Start Isaac Sim on Windows with the same `ROS_DOMAIN_ID` used by WSL2:

```powershell
$env:ROS_DOMAIN_ID="30"
cd C:\path\to\vision-guided-grasping
& "C:\path\to\isaac-sim\python.bat" sim\isaac\stage5_randomized_scene.py `
  --trial-id 0 `
  --seed 42 `
  --target-label cube `
  --save-usd outputs\stage5_trial_000.usd
```

The script publishes the same bridge topics as stage 3:

- `/camera/image_raw`
- `/camera/depth/image_rect_raw`
- `/camera/color/camera_info`
- `/joint_states`
- `/tf`
- `/clock`

It also subscribes to `/joint_command`, so the stage 4 grasp demo can still be used.

## Run Perception and Localization

In WSL2:

```bash
export ROS_DOMAIN_ID=30
cd ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
```

Run YOLO-World or the mock detector:

```bash
ros2 run yolo_world_ros yolo_world_node \
  --ros-args \
  -p text_prompt:=cube,box \
  -p confidence_threshold:=0.2 \
  -p model_config:=/home/$USER/YOLO-World/configs/pretrain/<config>.py \
  -p checkpoint_path:=/home/$USER/YOLO-World/weights/<checkpoint>.pth
```

Run localization:

```bash
ros2 run localization object_localizer_node \
  --ros-args \
  -p detections_topic:=/detections \
  -p depth_topic:=/camera/depth/image_rect_raw \
  -p camera_info_topic:=/camera/color/camera_info \
  -p target_frame:=base_link
```

For each trial, record the observed result row manually or with a small script. The result CSV must include all trial fields plus:

```text
detections_count,target_detected,mean_confidence,localized,localized_x,localized_y,localized_z
```

## Example Result CSV

```csv
trial_id,seed,light_intensity,table_color_r,table_color_g,table_color_b,object_color_r,object_color_g,object_color_b,camera_x,camera_y,camera_z,camera_roll,camera_pitch,camera_yaw,target_label,detections_count,target_detected,mean_confidence,localized,localized_x,localized_y,localized_z
0,478163327,703.5,0.42,0.58,0.33,0.82,0.14,0.31,0.56,-0.96,0.94,62.8,1.2,-0.5,cube,2,true,0.71,true,0.58,0.05,0.45
```

## Generate Report

```bash
ros2 run sim2real_eval summarize_results -- \
  --input outputs/sim2real_results.csv \
  --output outputs/sim2real_report.md
```

The report includes:

- total trials;
- target detection rate;
- localization success rate;
- mean confidence;
- localized point mean and standard deviation;
- worst-confidence trial table.

## Verification Checklist

- `python -m pytest` passes inside `ros2_ws/src/sim2real_eval`.
- `python -m compileall` passes for all Python packages and `sim/isaac`.
- `colcon build` finds `sim2real_eval` in WSL2 ROS2 Humble.
- At least one randomized Isaac scene publishes RGB-D, TF, and camera info.
- A sample result CSV produces `outputs/sim2real_report.md`.
