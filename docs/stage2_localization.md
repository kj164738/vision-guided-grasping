# Stage 2: RGB-D Localization and TF Transform

## Goal

Convert 2D detections from stage 1 into 3D target points:

```text
/detections
/camera/depth/image_rect_raw
/camera/color/camera_info
TF camera_color_optical_frame -> base_link
        |
        v
/localized_objects
/debug/object_points
```

## Interfaces

Inputs:

- `/detections` (`vision_msgs/msg/Detection2DArray`)
- `/camera/depth/image_rect_raw` (`sensor_msgs/msg/Image`)
- `/camera/color/camera_info` (`sensor_msgs/msg/CameraInfo`)
- TF from the detection frame, normally `camera_color_optical_frame`, to `base_link`

Outputs:

- `/localized_objects` (`vision_msgs/msg/Detection3DArray`)
- `/debug/object_points` (`geometry_msgs/msg/PoseArray`)

## Algorithm

For each 2D detection:

1. Read bbox center `(u, v)`.
2. Read a small depth window around `(u, v)`.
3. Keep finite depths inside `[min_depth_m, max_depth_m]`.
4. Use the median valid depth.
5. Back-project with camera intrinsics:

```text
x = (u - cx) * z / fx
y = (v - cy) * z / fy
z = depth
```

6. Transform the point into `target_frame`, default `base_link`.

`Detection3D.bbox.size` is set to zero in this stage because only object center localization is estimated.

## Run

Build in WSL2 Ubuntu 22.04:

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

Start a static transform for early testing:

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

Inspect outputs:

```bash
ros2 topic echo /localized_objects --once
ros2 topic echo /debug/object_points --once
```

In RViz2, add a `PoseArray` display for `/debug/object_points`.

## Validation

Success criteria:

- `/localized_objects` publishes `Detection3DArray` in `base_link`.
- `/debug/object_points` shows one pose per localized object.
- Invalid depth values are skipped instead of producing bad coordinates.
- Missing TF produces a warning and the node keeps running.

## Evidence Log

| Date | Command | Result | Notes |
| --- | --- | --- | --- |
| TBD | `colcon build` | TBD | TBD |
| TBD | static TF test | TBD | TBD |
| TBD | RGB-D localization test | TBD | TBD |
