"""Utility helpers for ClawSouls ROS2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: str | Path) -> dict[str, Any]:
    """Read and parse a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON as a dictionary.
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def read_text(path: str | Path) -> str:
    """Read a text file and return its contents.

    Args:
        path: Path to the text file.

    Returns:
        File contents as a string.
    """
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max.

    Args:
        value: The value to clamp.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.

    Returns:
        Clamped value.
    """
    return max(min_val, min(max_val, value))


def parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a semver-like version string into a tuple of ints.

    Args:
        version_str: Version string like '0.5' or '1.0.0'.

    Returns:
        Tuple of version components.
    """
    return tuple(int(x) for x in version_str.split('.'))
