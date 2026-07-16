"""The physical-robot half of the tether backend: controller_manager against
the hardware interface, plus the camera. Nothing here is shared with the sim.

Not an entry point — bringup.launch.py includes this when SIM=false, alongside
the description and control layers.

The camera runs with arm_stream:=false: the control port takes one client and
the hardware interface holds it for the whole session, so the driver sends
"stream on" itself and camera_node only reads the video port.

Before running: robot powered on, in direct-connection mode, this machine on
its Wi-Fi hotspot, ROBOMASTER_IP set in .env. Run `make tether-test` first —
it's a much faster failure signal than the full launch stack.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    camera_pkg = get_package_share_directory("robomaster_camera")

    # Passed down by bringup rather than $(find robomaster_bringup)'d here:
    # bringup includes this file, so reaching back into it would make the two
    # packages depend on each other.
    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[LaunchConfiguration("controllers_file")],
        output="screen",
    )

    camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(camera_pkg, "launch", "camera.launch.py")),
        launch_arguments={"arm_stream": "false"}.items(),
        condition=IfCondition(LaunchConfiguration("video")),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "controllers_file",
                description="Path to the controller_manager params (bringup owns it).",
            ),
            DeclareLaunchArgument(
                "video",
                default_value="true",
                choices=["true", "false"],
                description="Bring up the camera. Perception is separate — see bringup.",
            ),
            # Accepted and ignored: bringup passes sim to every include.
            DeclareLaunchArgument("sim", default_value="false", choices=["true", "false"]),
            controller_manager,
            # The video port has nothing to connect to until the driver has
            # activated and sent "stream on".
            TimerAction(period=5.0, actions=[camera]),
        ]
    )
