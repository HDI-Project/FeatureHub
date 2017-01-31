#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASEDIR=$(realpath ${SCRIPT_DIR}/..)
CONTAINER_NAME=app

# Testing
sudo rm -rf /var/lib/featurefactory/*
./kill_containers.sh $CONTAINER_NAME featurefactorymysql

# Create network
DOCKER_NETWORK_NAME="featurefactory-network"
docker network inspect $DOCKER_NETWORK_NAME >/dev/null 2>&1 \
    || docker network create $DOCKER_NETWORK_NAME

# Run build
docker run \
    -dit \
    --name $CONTAINER_NAME \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$BASEDIR:/tmp/ff:ro" \
    -v /var/lib/featurefactory:/var/lib/featurefactory \
    -p 443:443 \
    --network=$DOCKER_NETWORK_NAME \
    ubuntu /tmp/ff/deploy/test_container.sh

docker logs --follow $CONTAINER_NAME
