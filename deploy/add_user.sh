#!/usr/bin/env bash

# These environment variables are local
source .env

if [ "$#" != "2" ]; then
    echo "usage: ./add_user.sh ff_newuser_username ff_newuser_password"
    exit 1
fi

FF_NEWUSER_USERNAME=$1
FF_NEWUSER_PASSWORD=$2

echo "Creating new user: $FF_NEWUSER_USERNAME"

# Create user on host machine
# Change password. This is portable to ubuntu
docker exec -i $HUB_CONTAINER_NAME \
    bash <<EOF
useradd -m -s /bin/bash -U $FF_NEWUSER_USERNAME
echo $FF_NEWUSER_USERNAME:$FF_NEWUSER_PASSWORD | /usr/sbin/chpasswd
EOF

# Create directory for user notebooks and copy in templates. Will mount this
# later. Note that "the user ID has to match for mounted files". Remove admin
# notebooks.
mkdir -p $FF_DATA_DIR/users/$FF_NEWUSER_USERNAME/notebooks
cp -r ../notebooks/* $FF_DATA_DIR/users/$FF_NEWUSER_USERNAME/notebooks
rm -r $FF_DATA_DIR/users/$FF_NEWUSER_USERNAME/notebooks/admin

# Create user in database with correct permissions. Create .my.cnf file for
# user. The password for mysql db is generated randomly and is not the same as
# the system user account password.
FF_NEWUSER_MYSQL_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
docker exec -i $MYSQL_CONTAINER_NAME \
    mysql \
        --user=$MYSQL_ROOT_USERNAME \
        --password=$MYSQL_ROOT_PASSWORD <<EOF
CREATE USER '$FF_NEWUSER_USERNAME'@'%' IDENTIFIED BY '$FF_NEWUSER_MYSQL_PASSWORD';
GRANT INSERT, SELECT ON $MYSQL_DATABASE.* TO '$FF_NEWUSER_USERNAME'@'%';
EOF

cat >$FF_DATA_DIR/users/$FF_NEWUSER_USERNAME/.my.cnf <<EOF
[client]
user=$FF_NEWUSER_USERNAME
password=$FF_NEWUSER_MYSQL_PASSWORD
EOF

# User own all files in mounted volume
sudo chmod -R 777 $FF_DATA_DIR/users/$FF_ADMIN_USERNAME

echo "Creating new user: $FF_NEWUSER_USERNAME: Done."
