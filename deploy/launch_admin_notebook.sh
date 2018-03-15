#!/bin/bash

source .env
source .env.local >/dev/null 2>&1 || true

docker run -d \
    --name jpy-admin \
    --shm-size=16g \
    -v "${FF_DATA_DIR}/tmp:/tmp:rw" \
    -v "${FF_DATA_DIR}/data:/data:rw" \
    -v "${FF_DATA_DIR}/users/admin/:/home/jovyan:rw" \
    -v "${SECRETS_VOLUME_NAME}:/etc/letsencrypt:ro" \
    -v "$(pwd)/jupyter_notebook_config.py:/home/jovyan/.jupyter/jupyter_notebook_config.py:ro" \
    -w "/home/jovyan/notebooks" \
    -p 8888:8888 \
    --network ${DOCKER_NETWORK_NAME} \
    -e MYSQL_CONTAINER_NAME=${MYSQL_CONTAINER_NAME} \
    ${FF_CONTAINER_NAME} jupyter notebook
