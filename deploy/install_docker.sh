#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# ------------------------------------------------------------------------------
# Install docker

if [ "$PKG_MGR" = "apt-get" ]; then
    sudo apt-get install docker.io
elif [ "$PKG_MGR" = "yum" ]; then
    sudo yum install docker
fi

sudo usermod -aG docker $USER
docker pull jupyterhub/singleuser
