"""Personality node for ClawSouls ROS2.

A ROS2 node that subscribes to human input, calls an LLM API with the
soul's persona as system prompt, and publishes the robot's response.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger

from .soul_loader import build_system_prompt, load_soul

logger = logging.getLogger(__name__)


class PersonalityNode(Node):
    """ROS2 node that provides AI personality for a robot.

    Loads a ClawSouls soul package, maintains conversation history,
    and calls LLM APIs to generate contextual responses.
    """

    def __init__(self) -> None:
        super().__init__('personality_node')

        # Declare parameters
        self.declare_parameter('soul_path', '')
        self.declare_parameter('api_provider', 'anthropic')
        self.declare_parameter('api_key', '')
        self.declare_parameter('model', 'claude-sonnet-4-20250514')
        self.declare_parameter('max_turns', 20)

        # Load soul
        soul_path = self.get_parameter('soul_path').get_parameter_value().string_value
        if not soul_path:
            self.get_logger().error('soul_path parameter is required')
            raise ValueError('soul_path parameter is required')

        self._soul = load_soul(soul_path)
        self._system_prompt = build_system_prompt(self._soul)
        self._api_provider: str = self.get_parameter('api_provider').get_parameter_value().string_value
        self._api_key: str = self.get_parameter('api_key').get_parameter_value().string_value
        self._model: str = self.get_parameter('model').get_parameter_value().string_value
        self._max_turns: int = self.get_parameter('max_turns').get_parameter_value().integer_value

        # Conversation history
        self._history: list[dict[str, str]] = []

        # HTTP client
        self._http_client = httpx.Client(timeout=60.0)

        # Pub/Sub
        self._pub = self.create_publisher(String, '/robot_response', 10)
        self._sub = self.create_subscription(
            String, '/human_input', self._on_human_input, 10
        )

        # Service
        self._srv = self.create_service(Trigger, '/chat', self._handle_chat)
        self._last_input: str = ''

        self.get_logger().info(
            f"Personality node started with soul: "
            f"{self._soul['manifest'].get('name', 'unknown')}"
        )

    def _on_human_input(self, msg: String) -> None:
        """Handle incoming human input messages."""
        self._last_input = msg.data
        self.get_logger().info(f"Received input: {msg.data[:80]}...")

        response_text = self._call_llm(msg.data)

        response_msg = String()
        response_msg.data = response_text
        self._pub.publish(response_msg)
        self.get_logger().info(f"Published response: {response_text[:80]}...")

    def _handle_chat(
        self, request: Trigger.Request, response: Trigger.Response
    ) -> Trigger.Response:
        """Handle /chat service calls."""
        if self._last_input:
            response.success = True
            response.message = self._call_llm(self._last_input)
        else:
            response.success = False
            response.message = "No input received yet."
        return response

    def _call_llm(self, user_message: str) -> str:
        """Call the LLM API with the soul system prompt and user message.

        Args:
            user_message: The user's input text.

        Returns:
            The LLM's response text.
        """
        self._history.append({"role": "user", "content": user_message})

        # Trim history
        if len(self._history) > self._max_turns * 2:
            self._history = self._history[-(self._max_turns * 2):]

        try:
            if self._api_provider == "anthropic":
                response_text = self._call_anthropic()
            elif self._api_provider == "openai":
                response_text = self._call_openai()
            else:
                response_text = f"Unknown API provider: {self._api_provider}"
                self.get_logger().error(response_text)
                return response_text

            self._history.append({"role": "assistant", "content": response_text})
            return response_text

        except Exception as e:
            self.get_logger().error(f"LLM API error: {e}")
            # Remove the failed user message from history
            if self._history and self._history[-1]["role"] == "user":
                self._history.pop()
            return f"I'm sorry, I encountered an error: {e}"

    def _call_anthropic(self) -> str:
        """Call the Anthropic Messages API."""
        response = self._http_client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self._model,
                "max_tokens": 1024,
                "system": self._system_prompt,
                "messages": self._history,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]

    def _call_openai(self) -> str:
        """Call the OpenAI Chat Completions API."""
        messages = [{"role": "system", "content": self._system_prompt}]
        messages.extend(self._history)

        response = self._http_client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "messages": messages,
                "max_tokens": 1024,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def destroy_node(self) -> None:
        """Clean up resources."""
        self._http_client.close()
        super().destroy_node()


def main(args: list[str] | None = None) -> None:
    """Entry point for the personality node."""
    rclpy.init(args=args)
    node = PersonalityNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
