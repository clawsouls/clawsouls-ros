# 🤖 ClawSouls ROS2

[![ROS2 Humble](https://img.shields.io/badge/ROS2-Humble-blue)](https://docs.ros.org/en/humble/)
[![ROS2 Iron](https://img.shields.io/badge/ROS2-Iron-blue)](https://docs.ros.org/en/iron/)
[![ROS2 Jazzy](https://img.shields.io/badge/ROS2-Jazzy-blue)](https://docs.ros.org/en/jazzy/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)

**Give your robot a soul.** ClawSouls persona packages for ROS2.

Load [SoulSpec](https://soulspec.org) soul packages (`soul.json` + `SOUL.md`) and apply AI personas to your robots. Connects to LLM APIs (Anthropic/OpenAI) with the soul's persona as system prompt, while enforcing physical safety constraints from the soul manifest.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ /human_input │────▶│ personality_node  │────▶│ /robot_response │
│  (String)    │     │                  │     │  (String)       │
└─────────────┘     │  soul.json +     │     └─────────────────┘
                    │  SOUL.md → LLM   │
                    └──────────────────┘

┌──────────┐     ┌─────────────────┐     ┌───────────────┐
│ /cmd_vel  │────▶│ safety_monitor  │────▶│ /cmd_vel_safe │
│ (Twist)   │     │                 │     │ (Twist)       │
└──────────┘     │ maxSpeed clamp  │     └───────────────┘
                 │ contactPolicy   │
                 └────────┬────────┘
                          │
                          ▼
                 ┌────────────────┐
                 │ /safety_status │
                 │ (String/JSON)  │
                 └────────────────┘
```

## Quick Start

### Install

```bash
# Clone into your ROS2 workspace
cd ~/ros2_ws/src
git clone https://github.com/clawsouls/clawsouls-ros.git

# Install dependencies
pip install httpx pyyaml

# Build
cd ~/ros2_ws
colcon build --packages-select clawsouls_ros
source install/setup.bash
```

### Launch

```bash
# Launch with the included care-companion soul
ros2 launch clawsouls_ros soul_bringup.launch.py \
  soul:=./souls/care-companion \
  api_key:=your-api-key-here

# Or with OpenAI
ros2 launch clawsouls_ros soul_bringup.launch.py \
  soul:=./souls/care-companion \
  api_provider:=openai \
  api_key:=sk-... \
  model:=gpt-4o
```

### Test It

```bash
# Send a message
ros2 topic pub --once /human_input std_msgs/msg/String "data: 'Hello, how are you?'"

# Listen for responses
ros2 topic echo /robot_response

# Check safety status
ros2 topic echo /safety_status
```

## Nodes

### `personality_node`

Subscribes to human input, calls an LLM with the soul's persona, and publishes responses.

| Parameter      | Type   | Default                  | Description                    |
| -------------- | ------ | ------------------------ | ------------------------------ |
| `soul_path`    | string | —                        | Path to soul package directory |
| `api_provider` | string | `anthropic`              | LLM provider (anthropic/openai)|
| `api_key`      | string | —                        | API key                        |
| `model`        | string | `claude-sonnet-4-20250514` | Model name                     |
| `max_turns`    | int    | `20`                     | Max conversation history turns |

**Topics:**
- Subscribes: `/human_input` (`std_msgs/String`)
- Publishes: `/robot_response` (`std_msgs/String`)

**Services:**
- `/chat` (`std_srvs/Trigger`)

### `safety_monitor`

Enforces physical safety constraints from the soul manifest.

| Parameter     | Type   | Default | Description                    |
| ------------- | ------ | ------- | ------------------------------ |
| `soul_path`   | string | —       | Path to soul package directory |
| `status_rate` | float  | `1.0`   | Status publish rate (Hz)       |

**Topics:**
- Subscribes: `/cmd_vel` (`geometry_msgs/Twist`)
- Publishes: `/cmd_vel_safe` (`geometry_msgs/Twist`), `/safety_status` (`std_msgs/String`)

## Soul Packages

A soul package is a directory containing:

- `soul.json` — Manifest following [SoulSpec v0.5](https://soulspec.org) with embodied robotics extensions
- `SOUL.md` — Personality and behavioral guidelines in markdown
- Optional: `IDENTITY.md`, `VOICE.md`, `CONTEXT.md`

See [`souls/care-companion/`](souls/care-companion/) for a complete example.

## Example: Care Companion Robot

The included `care-companion` soul configures a gentle elderly care robot with:
- Warm, patient personality with concise communication
- Voice + touch-screen interaction modes
- 0.5 m/s max speed limit
- Gentle-contact safety policy
- Emergency stop support

## Download Souls from Registry

```python
from clawsouls_ros.soul_loader import download_soul

# Download from clawsouls.ai registry
soul = download_soul("clawsouls", "care-companion")
```

## ⚠️ Spec Version Compatibility

> This package is designed for **v0.5 souls with `environment: "physical"`**. The `safety_monitor` node enforces physical constraints (`maxSpeed`, `contactPolicy`) that only apply to embodied agents. If you're building a text-only agent, use `environment: "virtual"` in your `soul.json` — the [clawsouls](https://github.com/clawsouls/clawsouls) CLI package handles text-only deployment.

## Links

- [ClawSouls](https://clawsouls.ai) — Soul package registry
- [SoulSpec](https://soulspec.org) — Open specification for AI personas
- [SoulSpec v0.5 Robotics](https://soulspec.org/spec/v0.5#robotics) — Embodied AI extensions

## License

Apache-2.0 — see [LICENSE](LICENSE).
