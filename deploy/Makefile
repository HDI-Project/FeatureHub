include .env

.DEFAULT_GOAL=build

.PHONY: network build clean clean_all kill_containers log_hub kill_images build_user build_hub ssl help

help:
	@echo help

setup:
	sudo mkdir -p $(FF_DATA_DIR)/config/{jupyterhub,featurefactory}
	sudo chmod -R 777 $(FF_DATA_DIR)

clean: kill_containers kill_images remove_files

remove_files:
	rm -rf $(FF_DATA_DIR)/{users,config}	

kill_containers:
	@docker rm -f $(HUB_CONTAINER_NAME) $(MYSQL_CONTAINER_NAME) 2>/dev/null || echo "No hub/db containers found."
	@docker rm -f $(shell docker ps -a -q --filter name=^/${FF_CONTAINER_NAME}-.*$) 2>/dev/null || echo "No user containers found."

kill_images:
	@docker rmi -f $(HUB_IMAGE_NAME) $(FF_IMAGE_NAME) 2>/dev/null || echo "No images found."

network:
	@docker network inspect $(DOCKER_NETWORK_NAME) >/dev/null 2>&1 || docker network create $(DOCKER_NETWORK_NAME)

build: network build_user build_hub ssl

build_user: setup
	docker-compose -f docker-compose-user.yml build

build_hub: setup
	docker-compose -f docker-compose.yml build
	# TODO better way?
	cp ./jupyterhub_config.py $(FF_DATA_DIR)/config/jupyterhub/

log_hub:
	docker logs --follow $(HUB_CONTAINER_NAME)

ssl:
	./gen_ssl.sh

up:
	docker-compose -f docker-compose.yml up -d

down:
	docker-compose down
