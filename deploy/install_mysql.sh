#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e

if [ "$#" != "5" ]; then
    echo "usage: ./install_mysql.sh mysql_container_name mysql_database_name"
    echo "                          mysql_admin_username mysql_admin_password"
    echo "                          ff_data_dir"
    exit 1
fi

MYSQL_CONTAINER_NAME=$1
MYSQL_DATABASE_NAME=$2
FF_ADMIN_USERNAME=$3
FF_ADMIN_PASSWORD=$4
FF_DATA_DIR=$5

# ------------------------------------------------------------------------------
# Download mysql

docker pull mysql:$MYSQL_VERSION

# Create a mysql container, initialize the featurefactory database, and create
# an admin user account. Also create a random root password.
root_password=$(cat /dev/urandom | tr -dc 'a-f0-9' | fold -w 8 | head -n 1)
docker run \
    -dt \
    --name "$MYSQL_CONTAINER_NAME" \
    -e MYSQL_ROOT_PASSWORD=$root_password \
    -e "MYSQL_DATABASE=$MYSQL_DATABASE_NAME" \
    --network=$DOCKER_NETWORK_NAME \
    mysql

# Wait until mysqld is ready for connections. In the startup process, the
# message gets printed before we're really ready for connections.
grep -m 2 "mysqld: ready for connections." <(docker logs --follow "$MYSQL_CONTAINER_NAME")

echo "done"

# Create an admin account
# Create an admin account
${SCRIPT_DIR}/add_admin.sh $MYSQL_CONTAINER_NAME \
                           $MYSQL_DATABASE_NAME \
                           root \
                           $root_password \
                           $FF_ADMIN_USERNAME \
                           $FF_ADMIN_PASSWORD \
                           $FF_DATA_DIR
