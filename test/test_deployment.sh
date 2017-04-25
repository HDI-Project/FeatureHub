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
USER1_USERNAME=user1 USER2_USERNAME=user2 FF_CONTAINER_NAME=featurefactoryuser 
for USER_ in $USER1_USERNAME $USER2_USERNAME;
do
    docker cp ./test_${USER_}.py \
        ${FF_CONTAINER_NAME}-${USER_}:/tmp/test_${USER_}.py
    docker exec -u ${USER_} -i ${FF_CONTAINER_NAME}-${USER_} \
        /opt/conda/bin/python3 /tmp/test_${USER_}.py
done
