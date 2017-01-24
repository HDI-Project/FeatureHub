#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

MYSQL_VERSION=5.7

# ------------------------------------------------------------------------------
# Download mysql

docker pull mysql:$MYSQL_VERSION

# Create a mysql container, initialize the featurefactory database, and create
# an admin user account.
docker run \
    --name "$MYSQL_CONTAINER_NAME" \
    -e MYSQL_ONETIME_PASSWORD \
    -e "MYSQL_DATABASE=$MYSQL_DATABASE_NAME" \
    -e "MYSQL_USER=$MYSQL_ADMIN_USERNAME" \
    -e "MYSQL_PASSWORD=$MYSQL_ADMIN_PASSWORD" \
    mysql

# WIP create and authenticate a non-admin user.
# docker exec -it $MYSQL_CONTAINER_NAME mysql \
#     -u $MYSQL_ADMIN_USERNAME \
#     -p $MYSQL_ADMIN_PASSWORD \

