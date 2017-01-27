#!/usr/bin/env bash

# WIP

set -e

if [ "$#" != "1" ]; then
    echo "usage: ./remove_user.sh username"
    exit 1
fi

USERNAME=$1

userdel -r $

# # TODO delete user in database
# cat <<EOF
# DROP USER '$USERNAME'@'%';
# EOF
