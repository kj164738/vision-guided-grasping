from __future__ import annotations

import sys
from typing import Optional

import cv2
from cv_bridge import CvBridge
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class CameraSourceNode(Node):
    """Publish frames from OpenCV capture as ROS2 images."""

    def __init__(self) -> None:
        super().__init__("camera_source_node")

        self.declare_parameter("source_type", "camera")
        self.declare_parameter("camera_index", 0)
        self.declare_parameter("video_path", "")
        self.declare_parameter("loop_video", True)
        self.declare_parameter("fps", 30.0)
        self.declare_parameter("frame_id", "camera_color_optical_frame")
        self.declare_parameter("image_topic", "/camera/image_raw")

        self._source_type = self.get_parameter("source_type").value
        self._camera_index = int(self.get_parameter("camera_index").value)
        self._video_path = str(self.get_parameter("video_path").value)
        self._loop_video = bool(self.get_parameter("loop_video").value)
        self._fps = float(self.get_parameter("fps").value)
        self._frame_id = str(self.get_parameter("frame_id").value)
        image_topic = str(self.get_parameter("image_topic").value)

        self._bridge = CvBridge()
        self._publisher = self.create_publisher(Image, image_topic, 10)
        self._capture: Optional[cv2.VideoCapture] = self._open_capture()

        if self._capture is None or not self._capture.isOpened():
            raise RuntimeError(self._source_description() + " could not be opened")

        period = 1.0 / max(self._fps, 1.0)
        self._timer = self.create_timer(period, self._publish_frame)
        self.get_logger().info(
            f"Publishing {self._source_description()} to {image_topic} at {self._fps:.1f} FPS"
        )

    def destroy_node(self) -> bool:
        if self._capture is not None:
            self._capture.release()
        return super().destroy_node()

    def _open_capture(self) -> cv2.VideoCapture:
        if self._source_type == "camera":
            return cv2.VideoCapture(self._camera_index)
        if self._source_type == "video":
            if not self._video_path:
                raise ValueError("video_path must be set when source_type is 'video'")
            return cv2.VideoCapture(self._video_path)
        raise ValueError("source_type must be either 'camera' or 'video'")

    def _source_description(self) -> str:
        if self._source_type == "camera":
            return f"camera index {self._camera_index}"
        return f"video file '{self._video_path}'"

    def _publish_frame(self) -> None:
        if self._capture is None:
            return

        ok, frame = self._capture.read()
        if not ok:
            if self._source_type == "video" and self._loop_video:
                self._capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self._capture.read()
            if not ok:
                self.get_logger().warn(f"No frame available from {self._source_description()}")
                return

        message = self._bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = self._frame_id
        self._publisher.publish(message)


def main(args: Optional[list[str]] = None) -> None:
    rclpy.init(args=args)
    node: Optional[CameraSourceNode] = None
    try:
        node = CameraSourceNode()
        rclpy.spin(node)
    except Exception as exc:  # noqa: BLE001 - surface startup failures in ROS logs/stderr.
        if node is not None:
            node.get_logger().error(str(exc))
        else:
            print(f"camera_source_node failed: {exc}", file=sys.stderr)
        raise
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
