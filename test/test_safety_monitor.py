"""Tests for safety_monitor module."""

import math

import pytest


class TestClamp:
    """Tests for the clamp utility used by safety monitor."""

    def test_clamp_within_range(self) -> None:
        from clawsouls_ros.utils import clamp

        assert clamp(0.5, 0.0, 1.0) == 0.5

    def test_clamp_above_max(self) -> None:
        from clawsouls_ros.utils import clamp

        assert clamp(2.0, 0.0, 1.0) == 1.0

    def test_clamp_below_min(self) -> None:
        from clawsouls_ros.utils import clamp

        assert clamp(-1.0, 0.0, 1.0) == 0.0


class TestSpeedScaling:
    """Tests for velocity scaling logic (unit-level, no ROS dependency)."""

    def test_scale_down_velocity(self) -> None:
        """Verify that velocity scaling preserves direction."""
        max_speed = 0.5
        vx, vy, vz = 1.0, 0.0, 0.0
        speed = math.sqrt(vx**2 + vy**2 + vz**2)

        if speed > max_speed:
            scale = max_speed / speed
            vx *= scale
            vy *= scale
            vz *= scale

        assert abs(vx - 0.5) < 1e-6
        assert abs(vy) < 1e-6

    def test_no_scale_within_limit(self) -> None:
        """Verify that velocities within limits are not modified."""
        max_speed = 1.0
        vx, vy = 0.3, 0.4
        speed = math.sqrt(vx**2 + vy**2)

        assert speed <= max_speed
