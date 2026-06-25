from __future__ import annotations

import sys
from typing import Optional

from cv_bridge import CvBridge
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2D, Detection2DArray, ObjectHypothesisWithPose

from yolo_world_ros.detector import MockDetector, YoloWorldDetector, parse_text_prompt
from yolo_world_ros.visualization import draw_detections


class YoloWorldNode(Node):
    """ROS2 node that publishes open-vocabulary 2D detections."""

    def __init__(self) -> None:
        super().__init__("yolo_world_node")

        self.declare_parameter("image_topic", "/camera/image_raw")
        self.declare_parameter("detections_topic", "/detections")
        self.declare_parameter("debug_image_topic", "/debug/detection_image")
        self.declare_parameter("text_prompt", "cup,bottle,box")
        self.declare_parameter("confidence_threshold", 0.2)
        self.declare_parameter("device", "cuda:0")
        self.declare_parameter("model_config", "")
        self.declare_parameter("checkpoint_path", "")
        self.declare_parameter("max_detections", 100)
        self.declare_parameter("mock_detector", False)

        image_topic = str(self.get_parameter("image_topic").value)
        detections_topic = str(self.get_parameter("detections_topic").value)
        debug_image_topic = str(self.get_parameter("debug_image_topic").value)

        self._bridge = CvBridge()
        self._detector = self._create_detector()
        self._detections_pub = self.create_publisher(Detection2DArray, detections_topic, 10)
        self._debug_image_pub = self.create_publisher(Image, debug_image_topic, 10)
        self._image_sub = self.create_subscription(Image, image_topic, self._on_image, 10)

        self.get_logger().info(
            f"Subscribed to {image_topic}; publishing {detections_topic} and {debug_image_topic}"
        )

    def _create_detector(self):
        text_prompt = str(self.get_parameter("text_prompt").value)
        labels = parse_text_prompt(text_prompt)

        if bool(self.get_parameter("mock_detector").value):
            self.get_logger().warn("Using mock detector; no YOLO-World model will be loaded")
            return MockDetector(labels)

        model_config = str(self.get_parameter("model_config").value)
        checkpoint_path = str(self.get_parameter("checkpoint_path").value)
        if not model_config or not checkpoint_path:
            raise ValueError(
                "model_config and checkpoint_path are required unless mock_detector is true"
            )

        return YoloWorldDetector(
            model_config=model_config,
            checkpoint_path=checkpoint_path,
            text_prompt=text_prompt,
            device=str(self.get_parameter("device").value),
            confidence_threshold=float(self.get_parameter("confidence_threshold").value),
            max_detections=int(self.get_parameter("max_detections").value),
        )

    def _on_image(self, message: Image) -> None:
        try:
            image = self._bridge.imgmsg_to_cv2(message, desired_encoding="bgr8")
            detections = self._detector.detect(image)
        except Exception as exc:  # noqa: BLE001 - keep node alive and report frame failures.
            self.get_logger().error(f"Detection failed: {exc}")
            return

        detections_message = Detection2DArray()
        detections_message.header = message.header
        for detection in detections:
            detections_message.detections.append(_to_detection2d(detection))
        self._detections_pub.publish(detections_message)

        debug_image = draw_detections(image, detections)
        debug_message = self._bridge.cv2_to_imgmsg(debug_image, encoding="bgr8")
        debug_message.header = message.header
        self._debug_image_pub.publish(debug_message)


def _to_detection2d(detection) -> Detection2D:
    x1, y1, x2, y2 = detection.xyxy
    message = Detection2D()
    message.bbox.center.position.x = (x1 + x2) / 2.0
    message.bbox.center.position.y = (y1 + y2) / 2.0
    message.bbox.size_x = max(x2 - x1, 0.0)
    message.bbox.size_y = max(y2 - y1, 0.0)

    hypothesis = ObjectHypothesisWithPose()
    hypothesis.hypothesis.class_id = detection.label
    hypothesis.hypothesis.score = detection.score
    message.results.append(hypothesis)
    return message


def main(args: Optional[list[str]] = None) -> None:
    rclpy.init(args=args)
    node: Optional[YoloWorldNode] = None
    try:
        node = YoloWorldNode()
        rclpy.spin(node)
    except Exception as exc:  # noqa: BLE001 - surface startup failures in ROS logs/stderr.
        if node is not None:
            node.get_logger().error(str(exc))
        else:
            print(f"yolo_world_node failed: {exc}", file=sys.stderr)
        raise
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
