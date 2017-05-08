#!/usr/bin/env bash

set -e

source .env
source .env.local >/dev/null 2>&1 || true

archive_dir=$FF_DATA_DIR/archive
archive_name=$1
if [ ! -d "$archive_dir/$archive_name" ]; then
    mkdir -p $archive_dir/$archive_name
fi

sudo cp -r $FF_DATA_DIR/{config,data,users,problems,notebooks,log} $archive_dir/$archive_name
docker run --rm -it \
    -v ${MYSQL_DATA_VOLUME_NAME}:/var/lib/mysql \
    -v $archive_dir/$archive_name/db:/db \
    busybox cp -r /var/lib/mysql /db
