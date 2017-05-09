#!/usr/bin/env bash

set -e

source .env
source .env.local >/dev/null 2>&1 || true

docker exec -it ${MYSQL_CONTAINER_NAME} \
    mysql --user=${MYSQL_ROOT_USERNAME} \
          --password=${MYSQL_ROOT_PASSWORD}
