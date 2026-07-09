CONTAINER_NAME=ep-sim

.PHONY: build up down shell gazebo check-gpu

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

shell: up
	docker compose exec ep-sim bash

gazebo: up
	docker compose exec ep-sim bash -c "source /opt/ros/humble/setup.bash && ign gazebo empty.sdf -r --render-engine ogre"

check-gpu: up
	docker compose exec ep-sim nvidia-smi