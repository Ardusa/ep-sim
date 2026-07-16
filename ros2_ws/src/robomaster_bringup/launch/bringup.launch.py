"""The entry point. Brings up the whole robot on whichever backend SIM selects.

    SIM=true   -> Gazebo + gz_ros2_control
    SIM=false  -> the physical EP over its plaintext SDK, + camera

Either way you get the same TF tree, the same mecanum controller, the same
/cmd_vel_teleop and /cmd_vel_autonomy inputs, and the same AprilTag topics. The
backend is the only thing that changes.

SIM is read from the environment (set it in .env) and has no default: an unset
or misspelled value fails here, naming itself, rather than silently booting the
wrong backend. Same reasoning as ROBOMASTER_IP, which description.launch.py
requires when SIM=false.

    make bringup             # everything, backend per .env
    make bringup-teleop      # drive it
    make bringup-camera      # watch the raw stream
    make bringup-detection   # tags (already included here; use standalone)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def _sim_from_env() -> str:
    raw = os.environ.get("SIM")
    if raw is None or raw == "":
        raise RuntimeError(
            "SIM is not set. Set it in .env: SIM=true for Gazebo, SIM=false for "
            "the physical robot (which also needs ROBOMASTER_IP)."
        )
    value = raw.strip().lower()
    if value not in ("true", "false"):
        raise RuntimeError(f"SIM must be 'true' or 'false', got '{raw}'.")
    return value


def _backends(context, *args, **kwargs):
    sim = _sim_from_env()
    bringup_pkg = get_package_share_directory("robomaster_bringup")
    detection = LaunchConfiguration("detection").perform(context)

    def include(pkg, launch_file, **launch_args):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(get_package_share_directory(pkg), "launch", launch_file)
            ),
            launch_arguments={**launch_args, "sim": sim}.items(),
        )

    actions = [
        include("robomaster_bringup", "description.launch.py"),
        include("robomaster_bringup", "control.launch.py"),
    ]

    # The backend-specific half. Each one owns only what the other can't share:
    # Gazebo + spawn + bridges, or the hardware controller_manager + camera.
    actions.append(
        include("robomaster_gazebo", "sim.launch.py", headless=LaunchConfiguration("headless"))
        if sim == "true"
        else include(
            "robomaster_driver",
            "tether.launch.py",
            controllers_file=os.path.join(bringup_pkg, "config", "tether_controllers.yaml"),
        )
    )

    if detection == "true":
        actions.append(include("robomaster_detection", "detection.launch.py"))

    return actions


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "detection",
                default_value="true",
                choices=["true", "false"],
                description="Run the AprilTag detection + overlay pipeline.",
            ),
            DeclareLaunchArgument(
                "headless",
                default_value="false",
                choices=["true", "false"],
                description="Gazebo with no GUI. Ignored when SIM=false.",
            ),
            OpaqueFunction(function=_backends),
        ]
    )
