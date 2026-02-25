from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'clawsouls_ros'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=[
        'setuptools',
        'httpx',
        'pyyaml',
    ],
    zip_safe=True,
    maintainer='ClawSouls',
    maintainer_email='hello@clawsouls.ai',
    description='Give your robot a soul. ClawSouls persona packages for ROS2.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'personality_node = clawsouls_ros.personality_node:main',
            'safety_monitor = clawsouls_ros.safety_monitor:main',
        ],
    },
)
