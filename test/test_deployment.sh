#!/bin/bash

set -e

# initialize
cd ../deploy
source .env
source .env.local >/dev/null 2>&1 || true

# build
make clean_all
make build
make up
sleep 20 # wait to complete
./add_user.sh -a admin admin
./add_user.sh user user

# start admin container
HUB_API_URL="http://$HUB_CONTAINER_NAME:8080/hub/api"
ADMIN_USERNAME=admin
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
    '$HUB_API_URL/users/$ADMIN_USERNAME/server' 2>&1
EOF

# wait for it to start
sleep 5

# execute some lines
docker exec -u ${ADMIN_USERNAME} -i ${FF_CONTAINER_NAME}-${ADMIN_USERNAME} \
    bash <<EOF
echo true;
EOF
