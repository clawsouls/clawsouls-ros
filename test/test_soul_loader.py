"""Tests for soul_loader module."""

import json
import os
import tempfile
from pathlib import Path

import pytest


def _create_soul_dir(tmp: str, manifest: dict, soul_md: str = "") -> str:
    """Create a temporary soul directory for testing."""
    soul_dir = os.path.join(tmp, "test-soul")
    os.makedirs(soul_dir, exist_ok=True)
    with open(os.path.join(soul_dir, "soul.json"), "w") as f:
        json.dump(manifest, f)
    if soul_md:
        with open(os.path.join(soul_dir, "SOUL.md"), "w") as f:
            f.write(soul_md)
    return soul_dir


class TestLoadSoul:
    """Tests for load_soul function."""

    def test_load_basic_soul(self) -> None:
        from clawsouls_ros.soul_loader import load_soul

        with tempfile.TemporaryDirectory() as tmp:
            soul_dir = _create_soul_dir(
                tmp,
                {"specVersion": "0.5", "name": "test"},
                "# Test Soul\nHello world",
            )
            result = load_soul(soul_dir)
            assert result["manifest"]["name"] == "test"
            assert "SOUL.md" in result["files"]

    def test_missing_soul_json(self) -> None:
        from clawsouls_ros.soul_loader import load_soul

        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(FileNotFoundError):
                load_soul(tmp)

    def test_old_spec_version_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        from clawsouls_ros.soul_loader import load_soul

        with tempfile.TemporaryDirectory() as tmp:
            soul_dir = _create_soul_dir(
                tmp, {"specVersion": "0.3", "name": "old"}
            )
            import logging
            with caplog.at_level(logging.WARNING):
                load_soul(soul_dir)
            assert "below" in caplog.text.lower() or "embodied" in caplog.text.lower()


class TestBuildSystemPrompt:
    """Tests for build_system_prompt function."""

    def test_builds_from_soul_md(self) -> None:
        from clawsouls_ros.soul_loader import build_system_prompt

        soul = {
            "manifest": {"name": "test"},
            "files": {"SOUL.md": "# Test\nBe helpful."},
        }
        prompt = build_system_prompt(soul)
        assert "Be helpful" in prompt

    def test_includes_safety_info(self) -> None:
        from clawsouls_ros.soul_loader import build_system_prompt

        soul = {
            "manifest": {
                "name": "test",
                "safety": {
                    "physical": {"contactPolicy": "no-contact", "maxSpeed": 1.0}
                },
            },
            "files": {"SOUL.md": "# Test"},
        }
        prompt = build_system_prompt(soul)
        assert "no-contact" in prompt
        assert "1.0" in prompt

    def test_fallback_to_name(self) -> None:
        from clawsouls_ros.soul_loader import build_system_prompt

        soul = {"manifest": {"name": "fallback-bot", "description": "A bot."}, "files": {}}
        prompt = build_system_prompt(soul)
        assert "fallback-bot" in prompt
