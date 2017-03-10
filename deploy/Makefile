include .env
-include .env.local

.DEFAULT_GOAL=help

.PHONY: help
help:
	@echo "Manage FeatureFactory deployment"
	@echo ""
	@echo "Options:"
	@echo "    help: Display this help message."
	@echo "    build: Build images, create network and volumes, install jupyterhub config"
	@echo "    up: Launch the app, creating all necessary containers."
	@echo "    down: Shut down the app, removing all created containers."
	@echo "    clean: Remove all containers, user files, and config files"
	@echo "    clean_all: Clean, and additionally remove built images, remove network, and remove volumes"

.PHONY: setup_files
setup_files:
	sudo mkdir -p $(FF_DATA_DIR)/config/jupyterhub
	sudo chmod -R 777 $(FF_DATA_DIR)
	sudo chmod 700 $(FF_DATA_DIR)/config/jupyterhub

.PHONY: teardown_files
teardown_files:
	sudo rm -rf $(FF_DATA_DIR)/{users,config}	

.PHONY: clean_all
clean_all: kill_containers teardown_files kill_images kill_network kill_volumes

.PHONY: clean
clean: kill_containers teardown_files

.PHONY: kill_containers
kill_containers:
	@docker rm -f $(HUB_CONTAINER_NAME) $(MYSQL_CONTAINER_NAME) 2>/dev/null || echo "No hub/db containers found."
	@docker rm -f $(shell docker ps -a -q --filter name=^/${FF_CONTAINER_NAME}-.*$) 2>/dev/null || echo "No user containers found."

.PHONY: kill_images
kill_images:
	@docker rmi -f $(HUB_IMAGE_NAME) $(FF_IMAGE_NAME) 2>/dev/null || echo "No images found."

.PHONY: network
network:
	@docker network inspect $(DOCKER_NETWORK_NAME) >/dev/null 2>&1 || docker network create $(DOCKER_NETWORK_NAME)

.PHONY: kill_network
kill_network:
	@docker network inspect $(DOCKER_NETWORK_NAME) >/dev/null 2>&1 && docker network rm $(DOCKER_NETWORK_NAME) || echo "No network found."

.PHONY: volumes
volumes:
	@docker volume inspect $(MYSQL_DATA_VOLUME_NAME) >/dev/null 2>&1 || docker volume create --name $(MYSQL_DATA_VOLUME_NAME)
	@docker volume inspect $(SECRETS_VOLUME_NAME) >/dev/null 2>&1 || docker volume create --name $(SECRETS_VOLUME_NAME)

.PHONY: kill_volumes
kill_volumes:
	@docker volume inspect $(MYSQL_DATA_VOLUME_NAME) >/dev/null 2>&1 && docker volume rm $(MYSQL_DATA_VOLUME_NAME) || echo "No volumes found."
	@docker volume inspect $(SECRETS_VOLUME_NAME) >/dev/null 2>&1 && docker volume rm $(SECRETS_VOLUME_NAME) || echo "No volumes found."

.PHONY: build
build: build_user build_hub

.PHONY: build_user
build_user: network setup_files
	docker-compose -p $(FF_PROJECT_NAME) -f docker-compose-user.yml build

.PHONY: build_hub
build_hub: network volumes setup_files ssl
	docker-compose -p $(FF_PROJECT_NAME) -f docker-compose.yml build
	# TODO better way?
	sudo cp ./jupyterhub_config.py $(FF_DATA_DIR)/config/jupyterhub/
	sudo cp ./userlist $(FF_DATA_DIR)/config/jupyterhub/

.PHONY: ssl
ssl:
	./gen_ssl.sh

.PHONY: up
up:
	docker-compose -p $(FF_PROJECT_NAME) -f docker-compose.yml up -d

.PHONY: stop
stop:
	docker-compose -p $(FF_PROJECT_NAME) -f docker-compose.yml stop

.PHONY: start
start:
	docker-compose -p $(FF_PROJECT_NAME) -f docker-compose.yml start

.PHONY: down
down:
	docker-compose -p $(FF_PROJECT_NAME) -f docker-compose.yml down
