#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e
set -x

if [ "$#" != "4"]; then
    echo "usage: ./install_mysql.sh mysql_container_name mysql_database_name"
    echo "                          mysql_admin_username mysql_admin_password"
    exit 1
fi

MYSQL_CONTAINER_NAME=$1
MYSQL_DATABASE_NAME=$2
MYSQL_ADMIN_USERNAME=$3
MYSQL_ADMIN_PASSWORD=$4

docker_sudo=sudo

# ------------------------------------------------------------------------------
# Download mysql

${docker_sudo} docker pull mysql:$MYSQL_VERSION

# Create a mysql container, initialize the featurefactory database, and create
# an admin user account. Also create a random root password.
root_password=$(cat /dev/urandom | tr -dc 'a-f0-9' | fold -w 8 | head -n 1)
echo $root_password
${docker_sudo} docker run \
    --name "$MYSQL_CONTAINER_NAME" \
    -e MYSQL_ROOT_PASSWORD=$root_password \
    -e "MYSQL_DATABASE=$MYSQL_DATABASE_NAME" \
    -e "MYSQL_USER=$MYSQL_ADMIN_USERNAME" \
    -e "MYSQL_PASSWORD=$MYSQL_ADMIN_PASSWORD" \
    -d \
    mysql
