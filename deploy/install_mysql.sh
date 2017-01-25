#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e
set -x
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

MYSQL_VERSION=5.7

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
# an admin user account.
${docker_sudo} docker run \
    --name "$MYSQL_CONTAINER_NAME" \
    -e MYSQL_ONETIME_PASSWORD \
    -e "MYSQL_DATABASE=$MYSQL_DATABASE_NAME" \
    -e "MYSQL_USER=$MYSQL_ADMIN_USERNAME" \
    -e "MYSQL_PASSWORD=$MYSQL_ADMIN_PASSWORD" \
    mysql
