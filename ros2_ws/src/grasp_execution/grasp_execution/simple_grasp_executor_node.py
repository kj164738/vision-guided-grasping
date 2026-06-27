from __future__ import annotations

import sys
from typing import Optional

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from vision_msgs.msg import Detection3DArray

from grasp_execution.grasp_presets import get_grasp_preset, validate_all_grasp_presets
from grasp_execution.state_machine import GraspStateMachine, LocalizedTarget, choose_target
from sim_control.panda_presets import PANDA_JOINT_NAMES


class SimpleGraspExecutorNode(Node):
    """Run a lightweight grasp demo from localized semantic targets."""

    def __init__(self) -> None:
        super().__init__("simple_grasp_executor_node")
        validate_all_grasp_presets()

        self.declare_parameter("localized_objects_topic", "/localized_objects")
        self.declare_parameter("joint_command_topic", "/joint_command")
        self.declare_parameter("status_topic", "/grasp/status")
        self.declare_parameter("target_label", "")
        self.declare_parameter("auto_start", True)
        self.declare_parameter("publish_rate_hz", 10.0)
        self.declare_parameter("state_hold_seconds", 1.5)

        localized_objects_topic = str(self.get_parameter("localized_objects_topic").value)
        joint_command_topic = str(self.get_parameter("joint_command_topic").value)
        status_topic = str(self.get_parameter("status_topic").value)
        self._target_label = str(self.get_parameter("target_label").value)
        self._auto_start = bool(self.get_parameter("auto_start").value)
        self._publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
        self._state_hold_seconds = float(self.get_parameter("state_hold_seconds").value)
        self._ticks_per_state = max(int(round(self._state_hold_seconds * self._publish_rate_hz)), 1)

        self._state_machine = GraspStateMachine()
        self._target: Optional[LocalizedTarget] = None
        self._active = False
        self._tick_count = 0
        self._last_status = ""

        self._joint_pub = self.create_publisher(JointState, joint_command_topic, 10)
        self._status_pub = self.create_publisher(String, status_topic, 10)
        self._localized_sub = self.create_subscription(
            Detection3DArray,
            localized_objects_topic,
            self._on_localized_objects,
            10,
        )

        period = 1.0 / max(self._publish_rate_hz, 1.0)
        self._timer = self.create_timer(period, self._on_timer)
        self.get_logger().info(
            f"Waiting for localized targets on {localized_objects_topic}; "
            f"target_label='{self._target_label or '<first>'}'"
        )

    def _on_localized_objects(self, message: Detection3DArray) -> None:
        if self._active or self._state_machine.done:
            return

        targets = [_detection3d_to_target(detection) for detection in message.detections]
        target = choose_target(targets, self._target_label)
        if target is None:
            self._publish_status("idle: no matching target")
            return

        self._target = target
        self._publish_status(
            f"target_acquired: label={target.label or '<unknown>'} "
            f"score={target.score:.3f} position=({target.x:.3f}, {target.y:.3f}, {target.z:.3f})"
        )
        if self._auto_start:
            self._state_machine.start()
            self._active = True
            self._tick_count = 0

    def _on_timer(self) -> None:
        if not self._active:
            return

        state = self._state_machine.state
        preset_name = self._state_machine.current_preset_name()
        if preset_name is not None:
            self._publish_joint_command(preset_name)
            self._publish_status(f"{state}: publishing preset {preset_name}")
        elif state == "close_gripper":
            self._publish_status("close_gripper: gripper command reserved for stage 5")

        self._tick_count += 1
        if self._tick_count >= self._ticks_per_state:
            self._tick_count = 0
            next_state = self._state_machine.advance()
            self._publish_status(f"state_transition: {state} -> {next_state}")
            if self._state_machine.done:
                self._active = False
                self._publish_status("done: grasp demo completed")

    def _publish_joint_command(self, preset_name: str) -> None:
        preset = get_grasp_preset(preset_name)
        message = JointState()
        message.header.stamp = self.get_clock().now().to_msg()
        message.name = list(PANDA_JOINT_NAMES)
        message.position = list(preset.positions)
        self._joint_pub.publish(message)

    def _publish_status(self, text: str) -> None:
        if text == self._last_status:
            return
        self._last_status = text
        message = String()
        message.data = text
        self._status_pub.publish(message)
        self.get_logger().info(text)


def _detection3d_to_target(message) -> LocalizedTarget:
    label = ""
    score = 0.0
    if message.results:
        label = message.results[0].hypothesis.class_id
        score = float(message.results[0].hypothesis.score)

    position = message.bbox.center.position
    return LocalizedTarget(
        label=label,
        score=score,
        x=float(position.x),
        y=float(position.y),
        z=float(position.z),
    )


def main(args: Optional[list[str]] = None) -> None:
    rclpy.init(args=args)
    node: Optional[SimpleGraspExecutorNode] = None
    try:
        node = SimpleGraspExecutorNode()
        rclpy.spin(node)
    except Exception as exc:  # noqa: BLE001 - surface startup failures in ROS logs/stderr.
        if node is not None:
            node.get_logger().error(str(exc))
        else:
            print(f"simple_grasp_executor_node failed: {exc}", file=sys.stderr)
        raise
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
