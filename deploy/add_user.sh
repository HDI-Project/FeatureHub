#!/usr/bin/env bash

set -e

if [ "$#" != "6" ]; then
    echo "usage: ./add_user.sh mysql_container_name mysql_database_name"
    echo "                     mysql_admin_username mysql_admin_password"
    echo "                     mysql_newuser_username mysql_newuser_password"
    exit 1
fi

MYSQL_CONTAINER_NAME=$1
MYSQL_DATABASE_NAME=$2
MYSQL_ADMIN_USERNAME=$3
MYSQL_ADMIN_PASSWORD=$4
MYSQL_NEWUSER_USERNAME=$5
MYSQL_NEWUSER_PASSWORD=$6

# TODO
# Create user on host machine
# sudo useradd -M -N -u $MYSQL_NEWUSER_USERNAME -p $MYSQL_NEWUSER_PASSWORD

# Create directory for user's notebooks
# mkdir -p $FF_DATA_DIR/$MYSQL_NEWUSER_USERNAME/notebooks

# Copy notebook templates
# cp ${SCRIPT_DIR}/../notebooks/* $FF_DATA_DIR/$MYSQL_NEWUSER_USERNAME/notebooks

# Create user on in database
# Grant user permissions
# TODO research Socker Peer-Credential Authentication Plugin
#   (https://dev.mysql.com/doc/refman/5.5/en/socket-authentication-plugin.html)
docker_sudo=sudo
${docker_sudo} docker exec -i $MYSQL_CONTAINER_NAME \
    mysql \
        --user=$MYSQL_ADMIN_USERNAME \
        --password=$MYSQL_ADMIN_PASSWORD <<EOF
CREATE USER '$MYSQL_NEWUSER_USERNAME'@'%' IDENTIFIED BY '$MYSQL_NEWUSER_PASSWORD';
GRANT INSERT, SELECT ON $MYSQL_DATABASE_NAME.* TO '$MYSQL_NEWUSER_USERNAME'@'%';
EOF

echo "done"
