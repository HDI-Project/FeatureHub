#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONTAINER_NAME=app

# Testing
TEMPDIR=$(mktemp -d)
git clone https://github.com/HDI-Project/FeatureFactory $TEMPDIR

./kill_containers $CONTAINER_NAME featurefactorymysql

# Run build
docker run \
    -it -d --name $CONTAINER_NAME \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "${SCRIPT_DIR}:/tmp/deploy" \
    -v "${TEMPDIR}:/tmp/FeatureFactory_src" \
    ubuntu /tmp/deploy/test_container.sh

docker logs --follow $CONTAINER_NAME
