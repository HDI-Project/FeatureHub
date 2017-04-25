#!/bin/bash

set -e

# initialize
cd ../deploy
source .env
source .env.local >/dev/null 2>&1 || true

# test parameters
cd ../test
source .env.test >/dev/null 2>&1 || true
cd ../deploy

# build
make clean
make build
make up
sleep 15 # wait to complete

# create users
./add_user.sh -a ${ADMIN_USERNAME} ${ADMIN_PASSWORD}
./add_user.sh ${USER_USERNAME} ${USER_PASSWORD}

# start both containers
./api_client.py start-server ${ADMIN_USERNAME}
./api_client.py start-server ${USER_USERNAME}

# wait for it to start
sleep 5

# run tests
cd ../test

# admin initialization
docker cp ./test_admin.py ${FF_CONTAINER_NAME}-${ADMIN_USERNAME}:/tmp/test_admin.py
docker exec -u ${ADMIN_USERNAME} -i ${FF_CONTAINER_NAME}-${ADMIN_USERNAME} \
    /opt/conda/bin/python3 /tmp/test_admin.py

# user test
#USER_USERNAME=user FF_CONTAINER_NAME=featurefactoryuser 
docker cp ./test_user.py ${FF_CONTAINER_NAME}-${USER_USERNAME}:/tmp/test_user.py
docker exec -u ${USER_USERNAME} -i ${FF_CONTAINER_NAME}-${USER_USERNAME} /opt/conda/bin/python3 /tmp/test_user.py
