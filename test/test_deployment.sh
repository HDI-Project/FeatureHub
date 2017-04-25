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
./add_user.sh ${USER1_USERNAME} ${USER1_PASSWORD}
./add_user.sh ${USER2_USERNAME} ${USER2_PASSWORD}

# start all containers
./api_client.py start-server ${ADMIN_USERNAME}
./api_client.py start-server ${USER1_USERNAME}
./api_client.py start-server ${USER2_USERNAME}

# wait for it to start
sleep 5

# run tests
cd ../test

# admin initialization
#ADMIN_USERNAME=admin FF_CONTAINER_NAME=featurefactoryuser 
docker cp ./test_admin.py ${FF_CONTAINER_NAME}-${ADMIN_USERNAME}:/tmp/test_admin.py
docker exec -u ${ADMIN_USERNAME} -i ${FF_CONTAINER_NAME}-${ADMIN_USERNAME} \
    /opt/conda/bin/python3 /tmp/test_admin.py

# user1 test
#USER1_USERNAME=user1 FF_CONTAINER_NAME=featurefactoryuser 
docker cp ./test_user1.py ${FF_CONTAINER_NAME}-${USER1_USERNAME}:/tmp/test_user1.py
docker exec -u ${USER1_USERNAME} -i ${FF_CONTAINER_NAME}-${USER1_USERNAME} /opt/conda/bin/python3 /tmp/test_user.py

# user2 test
#USER2_USERNAME=user2 FF_CONTAINER_NAME=featurefactoryuser 
docker cp ./test_user2.py ${FF_CONTAINER_NAME}-${USER2_USERNAME}:/tmp/test_user2.py
docker exec -u ${USER2_USERNAME} -i ${FF_CONTAINER_NAME}-${USER2_USERNAME} /opt/conda/bin/python3 /tmp/test_user.py
