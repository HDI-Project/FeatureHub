#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONTAINER_NAME=testbuild
printf '\r\r\r\r\r\r\r\r' | \
docker run \
    -it --name $CONTAINER_NAME \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "${SCRIPT_DIR}:/tmp/deploy" \
    ubuntu /tmp/deploy/test_container.sh
