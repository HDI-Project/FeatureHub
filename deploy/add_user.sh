#!/usr/bin/env bash

set -e

# These environment variables are local
source .env

usage_and_exit() {
    echo "usage: add_user.sh [-a] username password" 1>&2
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
            usage_and_exit
            ;;
    esac
done
shift "$((OPTIND-1))"

if [ "$#" != "2" ]; then
    usage_and_exit
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
# Change password (syntax appears portable)
docker exec -i $HUB_CONTAINER_NAME \
    bash <<EOF
if id $_USERNAME >/dev/null 2>&1; then
    userdel $_USERNAME
fi
useradd -m -U $_USERNAME
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
sudo chmod -R 777 $FF_DATA_DIR/users/$_USERNAME

# Create user in database with correct permissions. Create .my.cnf file for
# user. The password for mysql db is generated randomly and is not the same as the system user account password.
_MYSQL_PASSWORD=$(openssl rand -hex 16)
if $admin; then
    cmd2="GRANT ALL ON *.* TO '$_USERNAME'@'%' WITH GRANT OPTION;"
else
    cmd2="GRANT INSERT, SELECT ON $MYSQL_DATABASE.* TO '$_USERNAME'@'%';"
fi

docker exec -i $MYSQL_CONTAINER_NAME \
    mysql \
        --user=$MYSQL_ROOT_USERNAME \
        --password=$MYSQL_ROOT_PASSWORD <<EOF
DROP USER IF EXISTS '$_USERNAME'@'%';
CREATE USER '$_USERNAME'@'%' IDENTIFIED BY '$_MYSQL_PASSWORD';
$cmd2
EOF

cat >$FF_DATA_DIR/users/$_USERNAME/.my.cnf <<EOF
[client]
user=$_USERNAME
password=$_MYSQL_PASSWORD
EOF

# Finally, add this user to the JupyterHub whitelist/admin list. The JupyterHub
# authenticator that handles this request will attempt to create the user, but
# we have already done this above because we wanted to set the password.
HUB_API_URL="http://$HUB_CONTAINER_NAME:8080/hub/api"
docker exec -u root -i $HUB_CONTAINER_NAME \
    bash <<EOF
cd $FF_DATA_DIR/config/jupyterhub
TOKEN=\$(jupyterhub token root)
wget \
    --quiet \
    -O- \
    --server-response \
    --method=POST \
    --header='Content-Type: application/json' \
    --header='Accept: application/json' \
    --header="Authorization: token \$TOKEN" \
    '$HUB_API_URL/users/$_USERNAME' 2>&1
EOF

if $admin; then
    docker exec -u root -i $HUB_CONTAINER_NAME \
        bash <<EOF
cd $FF_DATA_DIR/config/jupyterhub
TOKEN=\$(jupyterhub token root)
wget  \
    --quiet \
    -O- \
    --server-response \
    --method=PATCH \
    --header='Content-Type: application/json' \
    --header='Accept: application/json' \
    --header="Authorization: token \$TOKEN" \
    --body-data='{"admin": true}' \
    '$HUB_API_URL/users/$_USERNAME' 2>&1
EOF
fi

echo "Creating new $user_type: $_USERNAME: Done."
