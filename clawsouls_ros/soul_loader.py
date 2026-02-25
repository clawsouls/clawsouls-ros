"""Soul package loader for ClawSouls ROS2.

Loads soul.json manifests, referenced markdown files, and supports
downloading soul bundles from the ClawSouls registry API.
"""

from __future__ import annotations

import json
import logging
import os
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx

from .utils import parse_version, read_json, read_text

logger = logging.getLogger(__name__)

REGISTRY_BASE_URL = "https://clawsouls.ai/api/v1/bundle"
MIN_EMBODIED_VERSION = (0, 5)


def load_soul(path: str) -> dict[str, Any]:
    """Load a soul package from a directory.

    Reads soul.json and all referenced markdown files (SOUL.md, IDENTITY.md, etc.)
    from the given directory.

    Args:
        path: Path to the soul package directory.

    Returns:
        Dictionary with 'manifest' (parsed soul.json) and 'files' (dict of
        filename -> contents for referenced markdown files).

    Raises:
        FileNotFoundError: If soul.json is missing.
        json.JSONDecodeError: If soul.json is invalid.
    """
    soul_dir = Path(path)
    manifest_path = soul_dir / "soul.json"

    if not manifest_path.exists():
        raise FileNotFoundError(f"soul.json not found in {soul_dir}")

    manifest = read_json(manifest_path)
    files: dict[str, str] = {}

    # Load referenced markdown files
    for md_name in ["SOUL.md", "IDENTITY.md", "VOICE.md", "CONTEXT.md"]:
        md_path = soul_dir / md_name
        if md_path.exists():
            files[md_name] = read_text(md_path)

    # Check spec version for embodied features
    spec_version = manifest.get("specVersion", "0.1")
    version_tuple = parse_version(spec_version)
    if version_tuple < MIN_EMBODIED_VERSION:
        logger.warning(
            "Soul specVersion %s is below %s — embodied features "
            "(environment, safety.physical) may not be available.",
            spec_version,
            ".".join(str(v) for v in MIN_EMBODIED_VERSION),
        )

    return {"manifest": manifest, "files": files, "path": str(soul_dir)}


def download_soul(owner: str, name: str, dest: str | None = None) -> dict[str, Any]:
    """Download a soul bundle from the ClawSouls registry.

    Args:
        owner: Owner/organization of the soul package.
        name: Name of the soul package.
        dest: Local directory to extract to. Defaults to ./souls/{name}.

    Returns:
        Loaded soul dict (same as load_soul output).

    Raises:
        httpx.HTTPStatusError: If the registry request fails.
    """
    url = f"{REGISTRY_BASE_URL}/{owner}/{name}"
    dest_dir = Path(dest) if dest else Path("souls") / name
    dest_dir.mkdir(parents=True, exist_ok=True)

    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")

    if "application/zip" in content_type:
        with zipfile.ZipFile(BytesIO(response.content)) as zf:
            zf.extractall(dest_dir)
    elif "application/json" in content_type:
        bundle = response.json()
        # Write manifest
        with open(dest_dir / "soul.json", "w", encoding="utf-8") as f:
            json.dump(bundle.get("manifest", bundle), f, indent=2)
        # Write included files
        for filename, content in bundle.get("files", {}).items():
            with open(dest_dir / filename, "w", encoding="utf-8") as f:
                f.write(content)
    else:
        # Assume JSON
        with open(dest_dir / "soul.json", "w", encoding="utf-8") as f:
            f.write(response.text)

    return load_soul(str(dest_dir))


def build_system_prompt(soul: dict[str, Any]) -> str:
    """Build a system prompt from a loaded soul package.

    Concatenates SOUL.md and IDENTITY.md (if present) into a single
    system prompt string for LLM API calls.

    Args:
        soul: Loaded soul dict from load_soul().

    Returns:
        Combined system prompt string.
    """
    parts: list[str] = []
    files = soul.get("files", {})
    manifest = soul.get("manifest", {})

    # Identity first
    if "IDENTITY.md" in files:
        parts.append(files["IDENTITY.md"])

    # Soul personality
    if "SOUL.md" in files:
        parts.append(files["SOUL.md"])

    # Voice guidelines
    if "VOICE.md" in files:
        parts.append(files["VOICE.md"])

    # Context
    if "CONTEXT.md" in files:
        parts.append(files["CONTEXT.md"])

    # Add embodied context from manifest if available
    env = manifest.get("environment")
    if env:
        env_section = "\n## Embodiment\n"
        env_section += f"- Environment: {env.get('type', 'unknown')}\n"
        if "interactionMode" in env:
            mode = env["interactionMode"]
            if isinstance(mode, list):
                env_section += f"- Interaction modes: {', '.join(mode)}\n"
            else:
                env_section += f"- Interaction mode: {mode}\n"
        parts.append(env_section)

    # Add safety guidelines from manifest
    safety = manifest.get("safety", {})
    physical = safety.get("physical")
    if physical:
        safety_section = "\n## Physical Safety Constraints\n"
        if "contactPolicy" in physical:
            safety_section += f"- Contact policy: {physical['contactPolicy']}\n"
        if "maxSpeed" in physical:
            safety_section += f"- Maximum speed: {physical['maxSpeed']} m/s\n"
        parts.append(safety_section)

    if not parts:
        # Fallback to manifest name/description
        name = manifest.get("name", "Assistant")
        desc = manifest.get("description", "")
        parts.append(f"You are {name}. {desc}")

    return "\n\n".join(parts).strip()
