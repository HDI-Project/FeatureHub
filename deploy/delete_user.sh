#!/usr/bin/env bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$#" != "4" ]; then
    echo "usage: ./delete_user.sh mysql_container_name mysql_admin_username"
    echo "                     ff_username ff_data_dir"
    exit 1
fi

MYSQL_CONTAINER_NAME=$1
MYSQL_ADMIN_USERNAME=$2
FF_USERNAME=$3
FF_DATA_DIR=$4

userdel -f $FF_USERNAME
rm -rf $FF_DATA_DIR/users/$FF_USERNAME

docker cp "$FF_DATA_DIR/users/$MYSQL_ADMIN_USERNAME/.my.cnf" \
           $MYSQL_CONTAINER_NAME:/tmp/.my.cnf
docker exec -i $MYSQL_CONTAINER_NAME \
    mysql \
        --defaults-extra-file=/tmp/.my.cnf \
<<EOF
DROP USER '$FF_USERNAME';
EOF
docker exec $MYSQL_CONTAINER_NAME rm /tmp/.my.cnf
