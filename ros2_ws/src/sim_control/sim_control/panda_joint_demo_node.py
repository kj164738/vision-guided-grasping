from __future__ import annotations

import sys
from typing import Optional

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

from sim_control.panda_presets import PANDA_JOINT_NAMES, PRESETS, get_preset, validate_all_presets


class PandaJointDemoNode(Node):
    """Publish fixed Panda joint presets for Isaac Sim bridge validation."""

    def __init__(self) -> None:
        super().__init__("panda_joint_demo_node")
        validate_all_presets()

        self.declare_parameter("joint_command_topic", "/joint_command")
        self.declare_parameter("preset", "cycle")
        self.declare_parameter("publish_rate_hz", 10.0)
        self.declare_parameter("hold_seconds", 3.0)

        topic = str(self.get_parameter("joint_command_topic").value)
        self._preset = str(self.get_parameter("preset").value)
        self._publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
        self._hold_seconds = float(self.get_parameter("hold_seconds").value)
        self._publisher = self.create_publisher(JointState, topic, 10)
        self._tick_count = 0
        self._preset_index = 0
        self._cycle_presets = PRESETS

        if self._preset != "cycle":
            get_preset(self._preset)

        period = 1.0 / max(self._publish_rate_hz, 1.0)
        self._ticks_per_preset = max(int(round(self._hold_seconds * self._publish_rate_hz)), 1)
        self._timer = self.create_timer(period, self._publish_command)
        self.get_logger().info(
            f"Publishing Panda joint commands to {topic}; preset={self._preset}, "
            f"rate={self._publish_rate_hz:.1f} Hz"
        )

    def _publish_command(self) -> None:
        preset = self._current_preset()
        message = JointState()
        message.header.stamp = self.get_clock().now().to_msg()
        message.name = list(PANDA_JOINT_NAMES)
        message.position = list(preset.positions)
        self._publisher.publish(message)

        self._tick_count += 1
        if self._preset == "cycle" and self._tick_count % self._ticks_per_preset == 0:
            self._preset_index = (self._preset_index + 1) % len(self._cycle_presets)
            self.get_logger().info(f"Switching to Panda preset: {self._current_preset().name}")

    def _current_preset(self):
        if self._preset == "cycle":
            return self._cycle_presets[self._preset_index]
        return get_preset(self._preset)


def main(args: Optional[list[str]] = None) -> None:
    rclpy.init(args=args)
    node: Optional[PandaJointDemoNode] = None
    try:
        node = PandaJointDemoNode()
        rclpy.spin(node)
    except Exception as exc:  # noqa: BLE001 - surface startup failures in ROS logs/stderr.
        if node is not None:
            node.get_logger().error(str(exc))
        else:
            print(f"panda_joint_demo_node failed: {exc}", file=sys.stderr)
        raise
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
