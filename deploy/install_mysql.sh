#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e

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
echo $root_password #todo delete
${docker_sudo} docker run \
    --name "$MYSQL_CONTAINER_NAME" \
    -e MYSQL_ROOT_PASSWORD=$root_password \
    -e "MYSQL_DATABASE=$MYSQL_DATABASE_NAME" \
    -t -d \
    mysql

# Wait until mysqld is ready for connections. In the startup process, the
# message gets printed before we're really ready for connections.
grep -m 2 "mysqld: ready for connections." <(${docker_sudo} docker logs --follow "$MYSQL_CONTAINER_NAME")


${docker_sudo} docker exec -i "$MYSQL_CONTAINER_NAME" \
    mysql \
    --user=root \
    --password=${root_password} <<EOF
CREATE USER '$MYSQL_ADMIN_USERNAME'@'%' IDENTIFIED BY '$MYSQL_ADMIN_PASSWORD';
GRANT ALL ON *.* TO '$MYSQL_ADMIN_USERNAME'@'%' WITH GRANT OPTION;
EOF

echo "done"
