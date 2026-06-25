from __future__ import annotations

import sys
from typing import Optional

from cv_bridge import CvBridge
from geometry_msgs.msg import Pose, PoseArray
import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import CameraInfo, Image
import tf2_ros
from vision_msgs.msg import Detection3D, Detection3DArray, ObjectHypothesisWithPose
from vision_msgs.msg import Detection2DArray

from localization.depth import depth_image_to_meters
from localization.geometry import CameraIntrinsics, Point3D, Quaternion, Transform3D, transform_point
from localization.localizer import Detection2DCenter, localize_detections


class ObjectLocalizerNode(Node):
    """Convert 2D detections and aligned depth into 3D detections."""

    def __init__(self) -> None:
        super().__init__("object_localizer_node")

        self.declare_parameter("detections_topic", "/detections")
        self.declare_parameter("depth_topic", "/camera/depth/image_rect_raw")
        self.declare_parameter("camera_info_topic", "/camera/color/camera_info")
        self.declare_parameter("localized_objects_topic", "/localized_objects")
        self.declare_parameter("debug_points_topic", "/debug/object_points")
        self.declare_parameter("target_frame", "base_link")
        self.declare_parameter("depth_window_size", 5)
        self.declare_parameter("max_depth_m", 3.0)
        self.declare_parameter("min_depth_m", 0.05)
        self.declare_parameter("sync_tolerance_sec", 0.1)
        self.declare_parameter("tf_timeout_sec", 0.05)

        self._bridge = CvBridge()
        self._latest_depth: Optional[Image] = None
        self._latest_camera_info: Optional[CameraInfo] = None
        self._target_frame = str(self.get_parameter("target_frame").value)
        self._depth_window_size = int(self.get_parameter("depth_window_size").value)
        self._max_depth_m = float(self.get_parameter("max_depth_m").value)
        self._min_depth_m = float(self.get_parameter("min_depth_m").value)
        self._sync_tolerance_sec = float(self.get_parameter("sync_tolerance_sec").value)
        self._tf_timeout = Duration(seconds=float(self.get_parameter("tf_timeout_sec").value))

        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        detections_topic = str(self.get_parameter("detections_topic").value)
        depth_topic = str(self.get_parameter("depth_topic").value)
        camera_info_topic = str(self.get_parameter("camera_info_topic").value)
        localized_objects_topic = str(self.get_parameter("localized_objects_topic").value)
        debug_points_topic = str(self.get_parameter("debug_points_topic").value)

        self._localized_pub = self.create_publisher(
            Detection3DArray, localized_objects_topic, 10
        )
        self._debug_points_pub = self.create_publisher(PoseArray, debug_points_topic, 10)
        self._detections_sub = self.create_subscription(
            Detection2DArray, detections_topic, self._on_detections, 10
        )
        self._depth_sub = self.create_subscription(Image, depth_topic, self._on_depth, 10)
        self._camera_info_sub = self.create_subscription(
            CameraInfo, camera_info_topic, self._on_camera_info, 10
        )

        self.get_logger().info(
            f"Localizing {detections_topic} with {depth_topic}; publishing "
            f"{localized_objects_topic} in {self._target_frame}"
        )

    def _on_depth(self, message: Image) -> None:
        self._latest_depth = message

    def _on_camera_info(self, message: CameraInfo) -> None:
        self._latest_camera_info = message

    def _on_detections(self, message: Detection2DArray) -> None:
        if self._latest_depth is None or self._latest_camera_info is None:
            self.get_logger().warn("Waiting for depth image and camera_info before localizing")
            return

        if not self._within_tolerance(message.header.stamp, self._latest_depth.header.stamp):
            self.get_logger().warn("Skipping detections because depth image is outside sync tolerance")
            return

        try:
            depth_image = self._bridge.imgmsg_to_cv2(self._latest_depth, desired_encoding="passthrough")
            depth_m = depth_image_to_meters(depth_image, self._latest_depth.encoding)
            intrinsics = _intrinsics_from_camera_info(self._latest_camera_info)
            detections = [_detection2d_to_center(detection) for detection in message.detections]
            localized = localize_detections(
                detections=detections,
                depth_m=depth_m,
                intrinsics=intrinsics,
                depth_window_size=self._depth_window_size,
                min_depth_m=self._min_depth_m,
                max_depth_m=self._max_depth_m,
            )
            transform = self._lookup_transform(message.header.frame_id, message.header.stamp)
        except Exception as exc:  # noqa: BLE001 - report bad inputs without killing the node.
            self.get_logger().warn(f"Localization skipped: {exc}")
            return

        output = Detection3DArray()
        output.header.stamp = message.header.stamp
        output.header.frame_id = self._target_frame
        debug_points = PoseArray()
        debug_points.header = output.header

        for item in localized:
            point_target = transform_point(item.point_camera, transform)
            output.detections.append(_to_detection3d(point_target, item.label, item.score, output.header))
            debug_points.poses.append(_to_pose(point_target))

        self._localized_pub.publish(output)
        self._debug_points_pub.publish(debug_points)

    def _within_tolerance(self, detection_stamp, depth_stamp) -> bool:
        if _stamp_to_seconds(detection_stamp) == 0.0 or _stamp_to_seconds(depth_stamp) == 0.0:
            return True
        delta = abs(_stamp_to_seconds(detection_stamp) - _stamp_to_seconds(depth_stamp))
        return delta <= self._sync_tolerance_sec

    def _lookup_transform(self, source_frame: str, stamp) -> Transform3D:
        if not source_frame:
            raise ValueError("Detection header.frame_id is empty; cannot look up TF")

        transform = self._tf_buffer.lookup_transform(
            self._target_frame,
            source_frame,
            Time.from_msg(stamp),
            timeout=self._tf_timeout,
        )
        translation = transform.transform.translation
        rotation = transform.transform.rotation
        return Transform3D(
            translation=Point3D(translation.x, translation.y, translation.z),
            rotation=Quaternion(rotation.x, rotation.y, rotation.z, rotation.w),
        )


def _intrinsics_from_camera_info(message: CameraInfo) -> CameraIntrinsics:
    return CameraIntrinsics(
        fx=float(message.k[0]),
        fy=float(message.k[4]),
        cx=float(message.k[2]),
        cy=float(message.k[5]),
    )


def _detection2d_to_center(message) -> Detection2DCenter:
    label = ""
    score = 0.0
    if message.results:
        label = message.results[0].hypothesis.class_id
        score = float(message.results[0].hypothesis.score)

    return Detection2DCenter(
        u=float(message.bbox.center.position.x),
        v=float(message.bbox.center.position.y),
        label=label,
        score=score,
    )


def _to_detection3d(point: Point3D, label: str, score: float, header) -> Detection3D:
    message = Detection3D()
    message.header = header
    message.bbox.center = _to_pose(point)
    message.bbox.size.x = 0.0
    message.bbox.size.y = 0.0
    message.bbox.size.z = 0.0

    hypothesis = ObjectHypothesisWithPose()
    hypothesis.hypothesis.class_id = label
    hypothesis.hypothesis.score = score
    hypothesis.pose.pose = _to_pose(point)
    message.results.append(hypothesis)
    return message


def _to_pose(point: Point3D) -> Pose:
    pose = Pose()
    pose.position.x = point.x
    pose.position.y = point.y
    pose.position.z = point.z
    pose.orientation.w = 1.0
    return pose


def _stamp_to_seconds(stamp) -> float:
    return float(stamp.sec) + float(stamp.nanosec) * 1e-9


def main(args: Optional[list[str]] = None) -> None:
    rclpy.init(args=args)
    node: Optional[ObjectLocalizerNode] = None
    try:
        node = ObjectLocalizerNode()
        rclpy.spin(node)
    except Exception as exc:  # noqa: BLE001 - surface startup failures in ROS logs/stderr.
        if node is not None:
            node.get_logger().error(str(exc))
        else:
            print(f"object_localizer_node failed: {exc}", file=sys.stderr)
        raise
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
