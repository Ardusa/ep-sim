import os
from glob import glob

from setuptools import find_packages, setup

package_name = "robomaster_camera"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Ankur",
    maintainer_email="ardusa05@gmail.com",
    description="H.264 video acquisition from the physical RoboMaster EP.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "camera_node = robomaster_camera.camera_node:main",
        ],
    },
)
