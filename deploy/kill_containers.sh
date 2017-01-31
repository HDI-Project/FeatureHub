#!/usr/bin/env bash

if [ "$#" != "2" ]; then
    echo "usage: ./kill_containers.sh app_container_name mysql_container_name"
    exit 1
fi

CONTAINER_NAME=$1
MYSQL_CONTAINER_NAME=$2

# If test container already exists, then kill it
if [ "$(docker ps -a -f name=^/${CONTAINER_NAME}$ | wc -l)" != "1" ]; then
    docker rm -f ${CONTAINER_NAME}
fi

# Remove mysql containers
mysql_containers=$(docker ps -a --filter name=^/${MYSQL_CONTAINER_NAME}-.*$ \
    | awk '{print $NF}' \
    | tail -n +2)
if [ "$mysql_containers" != "" ]; then
    docker rm -f $mysql_containers
fi

# Remove jupyter containers
jupyter_containers=$(docker ps -a --filter name=^/jupyter-.*$ \
    | awk '{print $NF}' \
    | tail -n +2)
if [ "$jupyter_containers" != "" ]; then
    docker rm -f $jupyter_containers
fi
