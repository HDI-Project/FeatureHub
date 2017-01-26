#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONTAINER_NAME=testbuild

# If test container already exists, then kill it
if [ "$(docker ps -a -f name=^/${CONTAINER_NAME}$ | wc -l)" != "1" ]; then
    docker rm -f ${CONTAINER_NAME}
fi

# Remove mysql containers
docker ps -a --filter name=^/featurefactorymysql-.*$ \
    | awk '{print $NF}' \
    | tail -n +2 \
    | xargs docker rm -f

# Testing
TEMPDIR=$(mktemp -d)
git clone https://github.com/HDI-Project/FeatureFactory $TEMPDIR

# Run build
docker run \
    -it --name $CONTAINER_NAME \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "${SCRIPT_DIR}:/tmp/deploy" \
    -v "${TEMPDIR}:/tmp/FeatureFactory_src" \
    ubuntu /tmp/deploy/test_container.sh
