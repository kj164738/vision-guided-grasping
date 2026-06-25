# Stage 1: ROS2 + YOLO-World Perception

## Goal

Run an open-vocabulary detector in ROS2:

```text
/camera/image_raw -> yolo_world_ros -> /detections
                                \
                                 -> /debug/detection_image
```

## Environment

- Ubuntu 22.04 in WSL2
- ROS2 Humble
- Python 3.10
- Official YOLO-World repository installed in editable mode
- `vision_msgs` and `cv_bridge` installed from apt

## Build Checklist

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
ros2 pkg list | grep -E 'camera_source|yolo_world_ros'
```

## Camera Source

USB camera:

```bash
ros2 run camera_source camera_source_node \
  --ros-args \
  -p source_type:=camera \
  -p camera_index:=0 \
  -p frame_id:=camera_color_optical_frame \
  -p fps:=30.0
```

Video file:

```bash
ros2 run camera_source camera_source_node \
  --ros-args \
  -p source_type:=video \
  -p video_path:=/path/to/demo.mp4 \
  -p loop_video:=true \
  -p frame_id:=camera_color_optical_frame
```

## Detector

Mock detector for topic validation:

```bash
ros2 run yolo_world_ros yolo_world_node \
  --ros-args \
  -p mock_detector:=true \
  -p text_prompt:=cup,bottle,box
```

YOLO-World detector:

```bash
ros2 run yolo_world_ros yolo_world_node \
  --ros-args \
  -p text_prompt:=cup,bottle,box \
  -p confidence_threshold:=0.2 \
  -p device:=cuda:0 \
  -p model_config:=/home/$USER/YOLO-World/configs/pretrain/<config>.py \
  -p checkpoint_path:=/home/$USER/YOLO-World/weights/<checkpoint>.pth
```

## Validation

```bash
ros2 topic echo /camera/image_raw --once
ros2 topic echo /detections --once
rqt_image_view /debug/detection_image
```

Success criteria:

- `/camera/image_raw` publishes continuously.
- `/detections` contains bounding boxes, class hypotheses, and scores.
- `/debug/detection_image` shows boxes and labels over the original image.
- Missing model files produce a startup error that names the missing input.

## Evidence Log

Record results here after running in WSL2:

| Date | Command | Result | Notes |
| --- | --- | --- | --- |
| TBD | `colcon build` | TBD | TBD |
| TBD | mock detector run | TBD | TBD |
| TBD | YOLO-World detector run | TBD | TBD |
