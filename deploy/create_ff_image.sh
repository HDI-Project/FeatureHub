#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e

if [ "$#" != "3" ]; then
    echo "usage: ./create_ff_image.sh ff_image_name jupyterhub_config_dir"
    echo "                            mysql_container_name"
    exit 1
fi

FF_IMAGE_NAME=$1
JUPYTERHUB_CONFIG_DIR=$2
MYSQL_CONTAINER_NAME=$3

# ------------------------------------------------------------------------------

# Build image
docker build --tag $FF_IMAGE_NAME -f ./Dockerfile-user ./..

# mysql container name
# TODO move elsewhere
if [ ! -d "$JUPYTERHUB_CONFIG_DIR/featurefactory" ]; then
    mkdir -p "$JUPYTERHUB_CONFIG_DIR/featurefactory"
fi
cat <<EOF >>$JUPYTERHUB_CONFIG_DIR/featurefactory/featurefactory.conf
[mysql]
host = $MYSQL_CONTAINER_NAME
EOF
