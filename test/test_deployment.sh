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
sleep 20 # wait to complete

# create users
./add_user.sh -a ${ADMIN_USERNAME} ${ADMIN_PASSWORD}
./add_user.sh ${USER_USERNAME} ${USER_PASSWORD}

# start both containers
./api_client.py start-server ${ADMIN_USERNAME}
./api_client.py start-server ${USER_USERNAME}

# wait for it to start
sleep 5

# admin initialization
docker exec -u ${ADMIN_USERNAME} -i ${FF_CONTAINER_NAME}-${ADMIN_USERNAME} \
    /opt/conda/bin/python3 <<EOF
from featurefactory.admin.admin import Commands
admin_commands = Commands()
admin_commands.set_up(drop=True)

name = 'airbnb'
problem_type = 'classification'
data_path = '/data/airbnb'
files = ['train_users_2.csv', 'sessions.csv', 'countries.csv', 'age_gender_bkts.csv']
y_index = 0
y_column = 'country_destination'

admin_commands.create_problem(name, problem_type, data_path, files, y_index, y_column)
EOF

# user test
docker exec -u ${USER_USERNAME} -i ${FF_CONTAINER_NAME}-${USER_USERNAME} \
    /opt/conda/bin/python3 <<EOF
from featurefactory.problems import commands
dataset = commands.get_sample_dataset()

# import
# def example_feature(dataset):
#     return dataset[0][['age']].fillna(0)

import sys
import os
import shutil
if os.path.exists("/tmp/test"):
    shutil.rmtree("/tmp/test")
os.mkdir("/tmp/test")
with open("/tmp/test/example_feature.py", "w") as f:
    f.write("""\
def example_feature(dataset):
    return dataset[0][['age']].fillna(0)""")
sys.path.insert(0, "/tmp/test")
from example_feature import example_feature
sys.path.pop(0)

commands.evaluate(example_feature)
description="Age"
commands.register_feature(example_feature, description=description)
EOF
