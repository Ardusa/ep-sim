FROM osrf/ros:humble-desktop-full

RUN apt-get update && apt-get install -y \
    ros-humble-ros-gz \
    ros-humble-gz-ros2-control \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    ros-humble-teleop-twist-keyboard \
    ros-humble-joint-state-publisher \
    python3-colcon-common-extensions \
    ffmpeg \
    libgl1-mesa-dri \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc

WORKDIR /root/ros2_ws