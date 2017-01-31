#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e

# ------------------------------------------------------------------------------
# Install docker

if [ "$PKG_MGR" = "apt-get" ]; then
    apt-get -y install docker.io
elif [ "$PKG_MGR" = "yum" ]; then
    yum -y install docker
fi

# Note: at this point, we may need to start the docker daemon. For example, a
# missing step here on an Amazon AMI system would be `service docker
# start`. If we're running this from inside a testing container, then we've
# already mounted the host docker daemon socked to the guest container. On
# normal Ubuntu, meanwhile, I don't think an additional step to start the daemon
# is necessary.
