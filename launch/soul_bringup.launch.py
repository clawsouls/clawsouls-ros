"""Launch file for ClawSouls ROS2 soul bringup.

Usage:
    ros2 launch clawsouls_ros soul_bringup.launch.py soul:=./souls/care-companion
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """Generate launch description for ClawSouls nodes."""
    soul_arg = DeclareLaunchArgument(
        'soul',
        default_value='./souls/care-companion',
        description='Path to the soul package directory',
    )

    api_provider_arg = DeclareLaunchArgument(
        'api_provider',
        default_value='anthropic',
        description='LLM API provider (anthropic or openai)',
    )

    api_key_arg = DeclareLaunchArgument(
        'api_key',
        default_value='',
        description='API key for the LLM provider',
    )

    model_arg = DeclareLaunchArgument(
        'model',
        default_value='claude-sonnet-4-20250514',
        description='LLM model name',
    )

    personality_node = Node(
        package='clawsouls_ros',
        executable='personality_node',
        name='personality_node',
        parameters=[{
            'soul_path': LaunchConfiguration('soul'),
            'api_provider': LaunchConfiguration('api_provider'),
            'api_key': LaunchConfiguration('api_key'),
            'model': LaunchConfiguration('model'),
        }],
        output='screen',
    )

    safety_monitor_node = Node(
        package='clawsouls_ros',
        executable='safety_monitor',
        name='safety_monitor',
        parameters=[{
            'soul_path': LaunchConfiguration('soul'),
        }],
        output='screen',
    )

    return LaunchDescription([
        soul_arg,
        api_provider_arg,
        api_key_arg,
        model_arg,
        personality_node,
        safety_monitor_node,
    ])
