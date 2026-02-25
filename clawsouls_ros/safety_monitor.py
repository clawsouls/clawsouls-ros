"""Safety monitor node for ClawSouls ROS2.

Reads physical safety constraints from a soul.json manifest and enforces
velocity limits on /cmd_vel, publishing clamped commands to /cmd_vel_safe.
"""

from __future__ import annotations

import json
import logging
import math
from typing import Any

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import String

from .soul_loader import load_soul
from .utils import clamp

logger = logging.getLogger(__name__)


class SafetyMonitor(Node):
    """ROS2 node that enforces physical safety constraints from a soul package.

    Subscribes to /cmd_vel, clamps velocities to the soul's maxSpeed limit,
    and publishes safe commands to /cmd_vel_safe. Reports status on /safety_status.
    """

    def __init__(self) -> None:
        super().__init__('safety_monitor')

        # Parameters
        self.declare_parameter('soul_path', '')
        self.declare_parameter('status_rate', 1.0)

        soul_path = self.get_parameter('soul_path').get_parameter_value().string_value
        if not soul_path:
            self.get_logger().error('soul_path parameter is required')
            raise ValueError('soul_path parameter is required')

        # Load soul and extract safety config
        soul = load_soul(soul_path)
        manifest = soul['manifest']
        safety = manifest.get('safety', {})
        self._physical: dict[str, Any] = safety.get('physical', {})

        self._max_speed: float = self._physical.get('maxSpeed', float('inf'))
        self._contact_policy: str = self._physical.get('contactPolicy', 'none')
        self._violation_count: int = 0
        self._total_messages: int = 0

        # Publishers
        self._safe_pub = self.create_publisher(Twist, '/cmd_vel_safe', 10)
        self._status_pub = self.create_publisher(String, '/safety_status', 10)

        # Subscriber
        self._cmd_sub = self.create_subscription(
            Twist, '/cmd_vel', self._on_cmd_vel, 10
        )

        # Status timer
        status_rate = self.get_parameter('status_rate').get_parameter_value().double_value
        self._status_timer = self.create_timer(
            1.0 / max(status_rate, 0.1), self._publish_status
        )

        self.get_logger().info(
            f"Safety monitor started — maxSpeed: {self._max_speed} m/s, "
            f"contactPolicy: {self._contact_policy}"
        )

    def _on_cmd_vel(self, msg: Twist) -> None:
        """Process incoming velocity commands and enforce safety limits."""
        self._total_messages += 1

        # Compute linear speed magnitude
        linear_speed = math.sqrt(
            msg.linear.x ** 2 + msg.linear.y ** 2 + msg.linear.z ** 2
        )

        safe_msg = Twist()
        violated = False

        if linear_speed > self._max_speed and self._max_speed != float('inf'):
            # Scale down to max speed
            scale = self._max_speed / linear_speed
            safe_msg.linear.x = msg.linear.x * scale
            safe_msg.linear.y = msg.linear.y * scale
            safe_msg.linear.z = msg.linear.z * scale
            self._violation_count += 1
            violated = True
            self.get_logger().warn(
                f"Speed violation: {linear_speed:.2f} m/s > "
                f"{self._max_speed:.2f} m/s — clamping"
            )
        else:
            safe_msg.linear = msg.linear

        # Pass through angular (could add angular limits later)
        safe_msg.angular = msg.angular

        self._safe_pub.publish(safe_msg)

    def _publish_status(self) -> None:
        """Publish periodic safety status."""
        status = {
            "max_speed": self._max_speed,
            "contact_policy": self._contact_policy,
            "violation_count": self._violation_count,
            "total_messages": self._total_messages,
            "status": "ok" if self._violation_count == 0 else "violations_detected",
        }
        msg = String()
        msg.data = json.dumps(status)
        self._status_pub.publish(msg)


def main(args: list[str] | None = None) -> None:
    """Entry point for the safety monitor node."""
    rclpy.init(args=args)
    node = SafetyMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
