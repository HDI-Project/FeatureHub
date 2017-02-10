#!/usr/bin/env bash

set -e

# These environment variables are local
source .env

usage() {
    echo "usage: add_user.sh [-a] username password" 1>&2
    echo 1>&2
    echo "  -a  Create an admin user" 1>&2
    exit 1
}

admin=false
while getopts "a" opt; do
    case $opt in
        a)
            admin=true
            ;;
        *)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
    esac
done
shift "$((OPTIND-1))"

if [ "$#" != "2" ]; then
    usage
fi

_USERNAME=$1
_PASSWORD=$2

if $admin; then
    user_type="admin"
else
    user_type="user"
fi

echo "Creating new $user_type: $_USERNAME"

# Create user on host machine
# Change password. This is portable to ubuntu
docker exec -i $HUB_CONTAINER_NAME \
    bash <<EOF
useradd -m -s /bin/bash -U $_USERNAME
echo $_USERNAME:$_PASSWORD | /usr/sbin/chpasswd
EOF

# Create directory for user notebooks and copy in templates. Will mount this
# later. Note that "the user ID has to match for mounted files".
mkdir -p $FF_DATA_DIR/users/$_USERNAME/notebooks
if $admin; then
    cp -r ../notebooks/admin $FF_DATA_DIR/users/$_USERNAME/notebooks
else
    cp -r ../notebooks/* $FF_DATA_DIR/users/$_USERNAME/notebooks
    rm -r $FF_DATA_DIR/users/$_USERNAME/notebooks/admin
fi

# Create user in database with correct permissions. Create .my.cnf file for
# user. The password for mysql db is generated randomly and is not the same as the system user account password.
_MYSQL_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
if $admin; then
    cmd2="GRANT ALL ON *.* TO '$_USERNAME'@'%' WITH GRANT OPTION;"
else
    cmd2="GRANT INSERT, SELECT ON $MYSQL_DATABASE.* TO '$_USERNAME'@'%';"
fi

docker exec -i $MYSQL_CONTAINER_NAME \
    mysql \
        --user=$MYSQL_ROOT_USERNAME \
        --password=$MYSQL_ROOT_PASSWORD <<EOF
CREATE USER '$_USERNAME'@'%' IDENTIFIED BY '$_MYSQL_PASSWORD';
$cmd2
EOF

cat >$FF_DATA_DIR/users/$_USERNAME/.my.cnf <<EOF
[client]
user=$_USERNAME
password=$_MYSQL_PASSWORD
EOF

# Grant all permissions to all files in mounted volume
sudo chmod -R 777 $FF_DATA_DIR/users/$_USERNAME

echo "Creating new $user_type: $_USERNAME: Done."
