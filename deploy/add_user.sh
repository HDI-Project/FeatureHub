#!/usr/bin/env bash

# WIP
exit 1

# Create user on host machine
# Create directory for user's notebooks
# Copy notebook templates
# Create user on in database
# Grant user permissions
# TODO research Socker Peer-Credential Authentication Plugin
#   (https://dev.mysql.com/doc/refman/5.5/en/socket-authentication-plugin.html)
docker exec -it $MYSQL_CONTAINER_NAME \
    mysql \
        --user=$MYSQL_ADMIN_USERNAME \
        --password=$MYSQL_ADMIN_PASSWORD \
<<EOF
CREATE USER '$NEW_USER_NAME'@'%' IDENTIFIED BY '$NEW_USER_PASSWORD';
GRANT INSERT, SELECT ON $MYSQL_DATABASE_NAME.* TO '$NEW_USER_NAME'@'%';
exit;
EOF
