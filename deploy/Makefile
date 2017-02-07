include .env

.DEFAULT_GOAL=build

setup:
	sudo mkdir -p /var/lib/featurefactory/config/{jupyterhub,featurefactory}
	sudo chown -R ec2-user:ec2-user /var/lib/featurefactory

clean: setup
	rm -rf /var/lib/featurefactory/{users,config}	

# todo featurefactoryuser-.*
kill_containers:
	@docker rm -f featurefactoryhub featurefactorymysql >/dev/null 2>&1 || echo "No containers found."

kill_images:
	@docker rmi -f featurefactoryhub featurefactoryuser >/dev/null 2>&1 || echo "No images found."

clean_all: clean kill_containers kill_images

network:
	@docker network inspect featurefactory-network >/dev/null 2>&1 || docker network create featurefactory-network

build: network build_user build_hub ssl

build_user: setup
	docker-compose -f docker-compose-user.yml build

build_hub: setup
	docker-compose build
	cp ./jupyterhub_config.py /var/lib/featurefactory/config/jupyterhub/

log_hub:
	docker logs --follow featurefactoryhub

ssl:
	./gen_ssl.sh

up: build
	docker-compose -f docker-compose.yml up -d


.PHONY: network build clean clean_all kill_containers log_hub kill_images build_user build_hub ssl
