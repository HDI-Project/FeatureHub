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

# Install dockerspawner
# TODO move elsewhere
pip${PYTHON_VERSION} install dockerspawner

# Build image
docker build --tag $FF_IMAGE_NAME -f /tmp/ff/deploy/Dockerfile /tmp/ff

# mysql container name
# TODO move elsewhere
cat <<EOF >>$JUPYTERHUB_CONFIG_DIR/featurefactory
[mysql]
host = $MYSQL_CONTAINER_NAME
EOF
