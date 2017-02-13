include .env

.DEFAULT_GOAL=help

.PHONY: help setup_files teardown_files clean_all clean kill_containers kill_images network kill_network volumes kill_volumes build build_user build_hub ssl up down

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

setup_files:
	sudo mkdir -p $(FF_DATA_DIR)/config/{jupyterhub,featurefactory}
	sudo chmod -R 777 $(FF_DATA_DIR)

teardown_files:
	sudo rm -rf $(FF_DATA_DIR)/{users,config}	

clean_all: kill_containers teardown_files kill_images kill_network kill_volumes

clean: kill_containers teardown_files

kill_containers:
	@docker rm -f $(HUB_CONTAINER_NAME) $(MYSQL_CONTAINER_NAME) 2>/dev/null || echo "No hub/db containers found."
	@docker rm -f $(shell docker ps -a -q --filter name=^/${FF_CONTAINER_NAME}-.*$) 2>/dev/null || echo "No user containers found."

kill_images:
	@docker rmi -f $(HUB_IMAGE_NAME) $(FF_IMAGE_NAME) 2>/dev/null || echo "No images found."

network:
	@docker network inspect $(DOCKER_NETWORK_NAME) >/dev/null 2>&1 || docker network create $(DOCKER_NETWORK_NAME)

kill_network:
	@docker network inspect $(DOCKER_NETWORK_NAME) >/dev/null 2>&1 && docker network rm $(DOCKER_NETWORK_NAME) || echo "No network found."

volumes:
	@docker volume inspect $(MYSQL_DATA_VOLUME_NAME) >/dev/null 2>&1 || docker volume create --name $(MYSQL_DATA_VOLUME_NAME)

kill_volumes:
	@docker volume inspect $(FF_PROJECT_NAME)_$(MYSQL_DATA_VOLUME_NAME) >/dev/null 2>&1 && docker volume rm $(FF_PROJECT_NAME)_$(MYSQL_DATA_VOLUME_NAME) || echo "No volumes found."

build: build_user build_hub

build_user: network setup_files
	docker-compose -p $(FF_PROJECT_NAME) -f docker-compose-user.yml build

build_hub: network volumes setup_files ssl
	docker-compose -p $(FF_PROJECT_NAME) -f docker-compose.yml build
	# TODO better way?
	cp ./jupyterhub_config.py $(FF_DATA_DIR)/config/jupyterhub/
	cp ./userlist $(FF_DATA_DIR)/config/jupyterhub/

ssl:
	./gen_ssl.sh

up:
	docker-compose -p $(FF_PROJECT_NAME) -f docker-compose.yml up -d

down:
	docker-compose -p $(FF_PROJECT_NAME) -f docker-compose.yml down
