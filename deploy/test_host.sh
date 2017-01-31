#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASEDIR=$(realpath ${SCRIPT_DIR}/..)
CONTAINER_NAME=app

# Testing
sudo rm -rf /var/lib/featurefactory/*
./kill_containers.sh $CONTAINER_NAME featurefactorymysql

# Run build
docker run \
    -it -d --name $CONTAINER_NAME \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$BASEDIR:/tmp/ff:ro" \
    -v /var/lib/featurefactory:/var/lib/featurefactory \
    -p 443:443 \
    ubuntu /tmp/ff/deploy/test_container.sh

docker logs --follow $CONTAINER_NAME
