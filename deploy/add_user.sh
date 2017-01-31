#!/usr/bin/env bash

set -e

if [ "$#" != "7" ]; then
    echo "usage: ./add_user.sh mysql_container_name mysql_database_name"
    echo "                     mysql_admin_username mysql_admin_password"
    echo "                     ff_newuser_username ff_newuser_password"
    echo "                     ff_data_dir"
    exit 1
fi

MYSQL_CONTAINER_NAME=$1
MYSQL_DATABASE_NAME=$2
MYSQL_ADMIN_USERNAME=$3
MYSQL_ADMIN_PASSWORD=$4
FF_NEWUSER_USERNAME=$5
FF_NEWUSER_PASSWORD=$6
FF_DATA_DIR=$7

echo "Creating new user: $FF_NEWUSER_USERNAME"

# Create user on host machine
useradd -m -s /bin/bash -U $FF_NEWUSER_USERNAME

# Change password. This is portable to ubuntu
echo $FF_NEWUSER_USERNAME:$FF_NEWUSER_PASSWORD | /usr/sbin/chpasswd

# Create directory for user notebooks and copy in templates. Will mount this
# later. Note that "the user ID has to match for mounted files".
mkdir -p $FF_DATA_DIR/users/$FF_NEWUSER_USERNAME
cp -r ${SCRIPT_DIR}/../notebooks $FF_DATA_DIR/users/$FF_NEWUSER_USERNAME/notebooks
chown -R $FF_NEWUSER_USERNAME:$FF_NEWUSER_USERNAME $FF_DATA_DIR/users/$FF_NEWUSER_USERNAME

# Create user in database with correct permissions.
# TODO this could be a random password as it is saved below anyway.
docker exec -i $MYSQL_CONTAINER_NAME \
    mysql \
        --user=$MYSQL_ADMIN_USERNAME \
        --password=$MYSQL_ADMIN_PASSWORD <<EOF
CREATE USER '$FF_NEWUSER_USERNAME'@'%' IDENTIFIED BY '$FF_NEWUSER_PASSWORD';
GRANT INSERT, SELECT ON $MYSQL_DATABASE_NAME.* TO '$FF_NEWUSER_USERNAME'@'%';
EOF

# Create .my.cnf file for user. Or, can use mysql_config_editor such that
# password is not saved in plaintext.
cat >$FF_DATA_DIR/users/$FF_NEWUSER_USERNAME/.my.cnf <<EOF
[client]
host=$MYSQL_CONTAINER_NAME
user=$FF_NEWUSER_USERNAME
password=$FF_NEWUSER_PASSWORD
EOF

echo "Creating new user: $FF_NEWUSER_USERNAME: Done."
