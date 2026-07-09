CONTAINER_NAME=robomaster-sim
DC=docker compose
EXEC=$(DC) exec robomaster-sim bash -c
# source ROS + workspace overlay before any ros2/colcon command
SETUP=source /opt/ros/humble/setup.bash && cd /root/ros2_ws && [ -f install/setup.bash ] && source install/setup.bash;

.PHONY: build up down shell check-gpu build-ws launch sim rebuild clean

build:
	$(DC) build

up:
	$(DC) up -d

down:
	$(DC) down

shell: up
	$(DC) exec robomaster-sim bash

check-gpu: up
	$(DC) exec robomaster-sim nvidia-smi

build-ws: up
	$(EXEC) "$(SETUP) colcon build --symlink-install"

launch: up
	$(EXEC) "$(SETUP) ros2 launch robomaster_gazebo spawn.launch.py"

# build the workspace then launch — your daily one-shot
sim: build-ws launch

# nuke workspace build artifacts and rebuild from clean
rebuild: up
	$(EXEC) "cd /root/ros2_ws && rm -rf build install log && $(SETUP) colcon build --symlink-install"

clean: up
	$(EXEC) "cd /root/ros2_ws && rm -rf build install log"