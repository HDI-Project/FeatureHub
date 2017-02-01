#!/usr/bin/env bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

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

# Create user in database with correct permissions. Create .my.cnf file for
# user. The password for mysql db is generated randomly and is not the same as
# the system user account password.
FF_NEWUSER_MYSQL_PASSWORD=$(cat /dev/urandom | tr -dc 'a-f0-9' | fold -w 16 | head -n 1)
docker exec -i $MYSQL_CONTAINER_NAME \
    mysql \
        --user=$MYSQL_ADMIN_USERNAME \
        --password=$MYSQL_ADMIN_PASSWORD <<EOF
CREATE USER '$FF_NEWUSER_USERNAME'@'%' IDENTIFIED BY '$FF_NEWUSER_MYSQL_PASSWORD';
GRANT INSERT, SELECT ON $MYSQL_DATABASE_NAME.* TO '$FF_NEWUSER_USERNAME'@'%';
EOF

cat >$FF_DATA_DIR/users/$FF_NEWUSER_USERNAME/.my.cnf <<EOF
[client]
user=$FF_NEWUSER_USERNAME
password=$FF_NEWUSER_MYSQL_PASSWORD
EOF

# User own all files in mounted volume
chown -R $FF_NEWUSER_USERNAME:$FF_NEWUSER_USERNAME $FF_DATA_DIR/users/$FF_NEWUSER_USERNAME

echo "Creating new user: $FF_NEWUSER_USERNAME: Done."
