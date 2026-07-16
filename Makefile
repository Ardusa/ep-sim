# ---------------------------------------------------------------------------
# Host detection -> picks the right compose override automatically.
#   WSL2   : base + wsl2  (GPU + WSLg display, full Gazebo)
#   Mac    : base + mac   (no GPU, XQuartz display, port-mapped networking)
#   Linux  : base only
# ---------------------------------------------------------------------------
UNAME_S := $(shell uname -s)
IS_WSL  := $(shell grep -qi microsoft /proc/version 2>/dev/null && echo 1)

ifeq ($(IS_WSL),1)
  PLATFORM      := wsl2
  COMPOSE_FILES := -f docker-compose.yml -f docker-compose.wsl2.yml
else ifeq ($(UNAME_S),Darwin)
  PLATFORM      := mac
  COMPOSE_FILES := -f docker-compose.yml -f docker-compose.mac.yml
  X11 := $(shell defaults write org.xquartz.X11 nolisten_tcp -bool false; \
                 defaults write org.xquartz.X11 no_auth -bool true; \
                 pgrep -x Xquartz >/dev/null || { open -a XQuartz; sleep 3; })
else
  PLATFORM      := linux
  COMPOSE_FILES := -f docker-compose.yml
endif

DC   := docker compose $(COMPOSE_FILES)
EXEC := $(DC) exec robomaster-sim bash -c
SETUP := source /opt/ros/humble/setup.bash && cd /root/ros2_ws && [ -f install/setup.bash ] && source install/setup.bash;

.DEFAULT_GOAL := help
.PHONY: help image up down shell build test-gpu test-connection bringup \
        bringup-teleop bringup-camera bringup-detection rebuild clean

help: ## Show this help
	@echo "platform: $(PLATFORM)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'


# --- Container Lifecycle ----------------------------------------------------

image: ## Build the Docker image (rarely needed)
	$(DC) build

up: ## Start the container (detached)
	$(DC) up -d

down: ## Stop and remove the container
	$(DC) down

shell: up ## Open a bash shell in the container
	$(DC) exec robomaster-sim bash

build: up ## Colcon-build the ROS2 workspace
	$(EXEC) "$(SETUP) colcon build --symlink-install"


# --- Testing ---------------------------------------------------------------

test-gpu: up ## nvidia-smi inside the container (WSL2 only)
	$(DC) exec robomaster-sim nvidia-smi

test-connection: build ## Standalone TCP connectivity check against the real robot
	$(EXEC) "$(SETUP) ros2 run robomaster_driver connection_test"


# --- ROS2 Bringup -----------------------------------------------------------

bringup: build ## Bring up the robot (backend per SIM in .env)
ifneq ($(IS_WSL),1)
	@echo "NOTE: no GPU passthrough on '$(PLATFORM)'. If SIM=true, expect Gazebo to crawl (try HEADLESS=1)."
endif
	$(EXEC) "$(SETUP) ros2 launch robomaster_bringup bringup.launch.py \
	  headless:=$(if $(filter 1,$(HEADLESS)),true,false)"

bringup-teleop: up ## Drive with the keyboard (run alongside bringup)
	$(DC) exec robomaster-sim bash -c "$(SETUP) \
	  ros2 run teleop_twist_keyboard teleop_twist_keyboard \
	  --ros-args -r /cmd_vel:=/cmd_vel_teleop"

bringup-camera: up ## Watch the camera stream
	$(DC) exec robomaster-sim bash -c "$(SETUP) \
	  ros2 run rqt_image_view rqt_image_view /camera/image_raw"

bringup-detection: build ## AprilTag detection + overlay on its own
	$(EXEC) "$(SETUP) ros2 launch robomaster_detection detection.launch.py \
	  sim:=$${SIM}"


# --- Maintenance ------------------------------------------------------------

rebuild: up ## Nuke build artifacts and rebuild the workspace clean
	$(EXEC) "cd /root/ros2_ws && rm -rf build install log && $(SETUP) colcon build --symlink-install"

clean: up ## Remove workspace build artifacts
	$(EXEC) "cd /root/ros2_ws && rm -rf build install log"