"""Physical-robot backend: shared bringup + ros2_control against the
real RoboMaster EP over its plaintext SDK connection (robomaster_driver).

Counterpart to sim.launch.py, which loads Gazebo + gz_ros2_control
instead of this. Both include bringup.launch.py for rsp/TF; this one
additionally starts controller_manager against the physical hardware
interface and spawns the controllers defined in tether_controllers.yaml.

Before running this: robot powered on, in direct-connection mode, and
this machine joined to its Wi-Fi hotspot (default IP set in .env). If
you haven't verified basic connectivity yet, run
`ros2 run robomaster_driver connection_test` first - it's a much
faster failure signal than debugging through the full launch stack.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    gz_pkg = get_package_share_directory("robomaster_gazebo")
    driver_pkg = get_package_share_directory("robomaster_driver")

    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gz_pkg, "launch", "bringup.launch.py"))
    )

    controller_manager_config = os.path.join(driver_pkg, "config", "tether_controllers.yaml")

    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[controller_manager_config],
        output="screen",
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )

    wheel_velocity_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["wheel_velocity_controller"],
        output="screen",
    )

    return LaunchDescription(
        [
            bringup,
            controller_manager,
            joint_state_broadcaster_spawner,
            wheel_velocity_controller_spawner,
        ]
    )
