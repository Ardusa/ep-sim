"""Hardware backend: shared bringup + physical RoboMaster driver.

SCAFFOLDING. Includes bringup.launch.py so the TF tree / robot_description
are live, then logs a placeholder where the C++ DJI WiFi driver node will go.

When the driver lands, replace the LogInfo with the driver Node, e.g.:

    driver = Node(
        package='robomaster_driver',
        executable='robomaster_driver_node',
        output='screen',
        parameters=[{'robot_ip': '192.168.2.1'}],
    )

The driver subscribes to the same cmd_vel/controller interface the sim drives,
so nothing else in this file changes.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    gz_pkg = get_package_share_directory("robomaster_gazebo")

    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gz_pkg, "launch", "bringup.launch.py"))
    )

    return LaunchDescription(
        [
            bringup,
            LogInfo(
                msg="[tether] bringup live. DJI WiFi driver node not yet "
                "implemented — this is a placeholder."
            ),
        ]
    )
