#!/usr/bin/env bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$#" != "6" ]; then
    echo "usage: ./add_user.sh mysql_container_name mysql_database_name"
    echo "                     mysql_admin_username"
    echo "                     ff_newuser_username ff_newuser_password"
    echo "                     ff_data_dir"
    exit 1
fi

MYSQL_CONTAINER_NAME=$1
MYSQL_DATABASE_NAME=$2
MYSQL_ADMIN_USERNAME=$3
FF_NEWUSER_USERNAME=$4
FF_NEWUSER_PASSWORD=$5
FF_DATA_DIR=$6

echo "Creating new user: $FF_NEWUSER_USERNAME"

# Create user on host machine
useradd -m -s /bin/bash -U $FF_NEWUSER_USERNAME

# Change password. This is portable to ubuntu
echo $FF_NEWUSER_USERNAME:$FF_NEWUSER_PASSWORD | /usr/sbin/chpasswd

# Create directory for user notebooks and copy in templates. Will mount this
# later. Note that "the user ID has to match for mounted files". Remove admin
# notebooks.
mkdir -p $FF_DATA_DIR/users/$FF_NEWUSER_USERNAME
cp -r ${SCRIPT_DIR}/../notebooks $FF_DATA_DIR/users/$FF_NEWUSER_USERNAME/notebooks
rm -r $FF_DATA_DIR/users/$FF_NEWUSER_USERNAME/notebooks/admin

# Create user in database with correct permissions. Create .my.cnf file for
# user. The password for mysql db is generated randomly and is not the same as
# the system user account password. Since we don't track the admin password, we
# copy the admin config file to the database server, use that to log in, and
# then delete it. (TODO improve that.)
FF_NEWUSER_MYSQL_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
docker cp "$FF_DATA_DIR/users/$MYSQL_ADMIN_USERNAME/.my.cnf" \
           $MYSQL_CONTAINER_NAME:/tmp/.my.cnf
docker exec -i $MYSQL_CONTAINER_NAME \
    mysql \
        --defaults-extra-file=/tmp/.my.cnf \
<<EOF
CREATE USER '$FF_NEWUSER_USERNAME'@'%' IDENTIFIED BY '$FF_NEWUSER_MYSQL_PASSWORD';
GRANT INSERT, SELECT ON $MYSQL_DATABASE_NAME.* TO '$FF_NEWUSER_USERNAME'@'%';
EOF
docker exec $MYSQL_CONTAINER_NAME rm /tmp/.my.cnf

cat >$FF_DATA_DIR/users/$FF_NEWUSER_USERNAME/.my.cnf <<EOF
[client]
user=$FF_NEWUSER_USERNAME
password=$FF_NEWUSER_MYSQL_PASSWORD
EOF

# User own all files in mounted volume
chown -R $FF_NEWUSER_USERNAME:$FF_NEWUSER_USERNAME $FF_DATA_DIR/users/$FF_NEWUSER_USERNAME

echo "Creating new user: $FF_NEWUSER_USERNAME: Done."
