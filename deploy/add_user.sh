#!/usr/bin/env bash

# TODO
# Create user on host machine
# Create directory for user's notebooks
# Copy notebook templates

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

# Create user on in database
# Grant user permissions
# TODO research Socker Peer-Credential Authentication Plugin
#   (https://dev.mysql.com/doc/refman/5.5/en/socket-authentication-plugin.html)
docker_sudo=sudo
${docker_sudo} docker exec -it $MYSQL_CONTAINER_NAME \
    mysql \
        -u $MYSQL_ADMIN_USERNAME \
        -p $MYSQL_ADMIN_PASSWORD \
<<EOF
CREATE USER '$MYSQL_NEWUSER_USERNAME'@'%' IDENTIFIED BY '$MYSQL_NEWUSER_PASSWORD';
GRANT INSERT, SELECT ON $MYSQL_DATABASE_NAME.* TO '$MYSQL_NEWUSER_USERNAME'@'%';
exit;
EOF
