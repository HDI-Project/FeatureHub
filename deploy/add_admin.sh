#!/usr/bin/env bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$#" != "7" ]; then
    echo "usage: ./add_admin.sh mysql_container_name mysql_database_name"
    echo "                     mysql_root_username mysql_root_password"
    echo "                     ff_newuser_username ff_newuser_password"
    echo "                     ff_data_dir"
    exit 1
fi

MYSQL_CONTAINER_NAME=$1
MYSQL_DATABASE_NAME=$2
MYSQL_ROOT_USERNAME=$3
MYSQL_ROOT_PASSWORD=$4
FF_ADMIN_USERNAME=$5
FF_ADMIN_PASSWORD=$6
FF_DATA_DIR=$7

echo "Creating new user: $FF_ADMIN_USERNAME"

# Create user on host machine
useradd -m -s /bin/bash -U $FF_ADMIN_USERNAME

# Change password. This is portable to ubuntu
echo $FF_ADMIN_USERNAME:$FF_ADMIN_PASSWORD | /usr/sbin/chpasswd

# Create directory for user notebooks and copy in templates. Will mount this
# later. Note that "the user ID has to match for mounted files".
mkdir -p $FF_DATA_DIR/users/$FF_ADMIN_USERNAME
cp -r ${SCRIPT_DIR}/../notebooks $FF_DATA_DIR/users/$FF_ADMIN_USERNAME/notebooks

# Create user in database with correct permissions. Create .my.cnf file for
# user. The password for mysql db is generated randomly and is not the same as
# the system user account password.
FF_ADMIN_MYSQL_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
docker exec -i $MYSQL_CONTAINER_NAME \
    mysql \
        --user=$MYSQL_ROOT_USERNAME \
        --password=$MYSQL_ROOT_PASSWORD <<EOF
CREATE USER '$FF_ADMIN_USERNAME'@'%' IDENTIFIED BY '$FF_ADMIN_MYSQL_PASSWORD';
GRANT ALL ON *.* TO '$FF_ADMIN_USERNAME'@'%' WITH GRANT OPTION;
EOF

cat >$FF_DATA_DIR/users/$FF_ADMIN_USERNAME/.my.cnf <<EOF
[client]
user=$FF_ADMIN_USERNAME
password=$FF_ADMIN_MYSQL_PASSWORD
EOF

# User own all files in mounted volume
chown -R $FF_ADMIN_USERNAME:$FF_ADMIN_USERNAME $FF_DATA_DIR/users/$FF_ADMIN_USERNAME

echo "Creating new admin: $FF_ADMIN_USERNAME: Done."
