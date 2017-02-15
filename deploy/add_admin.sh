#!/usr/bin/env bash

# These environment variables are local
source .env

if [ "$#" != "2" ]; then
    echo "usage: ./add_admin.sh ff_admin_username ff_admin_password"
    exit 1
fi

FF_ADMIN_USERNAME=$1
FF_ADMIN_PASSWORD=$2

echo "Creating new user: $FF_ADMIN_USERNAME"

# Create user on host machine
# Change password. This is portable to ubuntu
docker exec -i $HUB_CONTAINER_NAME \
    bash <<EOF
useradd -m -s /bin/bash -U $FF_ADMIN_USERNAME
echo $FF_ADMIN_USERNAME:$FF_ADMIN_PASSWORD | /usr/sbin/chpasswd
EOF

# Create directory for user notebooks and copy in templates. Will mount this
# later. Note that "the user ID has to match for mounted files".
mkdir -p $FF_DATA_DIR/users/$FF_ADMIN_USERNAME
cp -r ../notebooks $FF_DATA_DIR/users/$FF_ADMIN_USERNAME/notebooks

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

# Grant all permissions to all files in mounted volume
sudo chmod -R 777 $FF_DATA_DIR/users/$FF_ADMIN_USERNAME

echo "Creating new admin: $FF_ADMIN_USERNAME: Done."
