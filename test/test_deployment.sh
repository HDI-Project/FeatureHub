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
make ssl
make up
sleep 15 # wait to complete

# create users
./users.py add ${ADMIN_USERNAME} ${ADMIN_PASSWORD} --admin=True
./users.py add ${USER1_USERNAME} ${USER1_PASSWORD}
./users.py add ${USER2_USERNAME} ${USER2_PASSWORD}
./users.py add ${USER3_USERNAME} ${USER3_PASSWORD}

# start all containers
./hub_client.py start-server ${ADMIN_USERNAME}
./hub_client.py start-server ${USER1_USERNAME}
./hub_client.py start-server ${USER2_USERNAME}
./hub_client.py start-server ${USER3_USERNAME}

# wait for it to start
sleep 5

# run tests
cd ../test

# admin initialization
# ADMIN_USERNAME=admin FF_CONTAINER_NAME=featurehubuser 
docker cp ./test_admin.py ${FF_CONTAINER_NAME}-${ADMIN_USERNAME}:/tmp/test_admin.py
docker exec -u ${ADMIN_USERNAME} -i ${FF_CONTAINER_NAME}-${ADMIN_USERNAME} \
    /opt/conda/bin/ipython /tmp/test_admin.py

# user1 test
# USER1_USERNAME=demo USER2_USERNAME=airbnb USER3_USERNAME=sberbank FF_CONTAINER_NAME=featurehubuser 
for USER_ in $USER1_USERNAME $USER2_USERNAME $USER3_USERNAME;
do
    docker cp ./test_${USER_}.py \
        ${FF_CONTAINER_NAME}-${USER_}:/tmp/test_${USER_}.py
    docker exec -u ${USER_} -i ${FF_CONTAINER_NAME}-${USER_} \
        /opt/conda/bin/ipython /tmp/test_${USER_}.py
done
