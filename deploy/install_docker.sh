#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e
set -x

# ------------------------------------------------------------------------------
# Install docker

if [ "$PKG_MGR" = "apt-get" ]; then
    sudo apt-get -y install docker.io
elif [ "$PKG_MGR" = "yum" ]; then
    sudo yum -y install docker
fi

# Note: at this point, we may need to start the docker daemon. For example, a
# missing step here on an Amazon AMI system would be `sudo service docker
# start`. If we're running this from inside a testing container, then we've
# already mounted the host docker daemon socked to the guest container. On
# normal Ubuntu, meanwhile, I don't think an additional step to start the daemon
# is necessary.

sudo usermod -aG docker $USER

# Now, the user needs to "logout" and "login" for the group changes to take
# effect. Hard to figure out how to emulate this when we've run a script using
# `su username`. Looks like we can't "patch" this by doing the usermod before
# even running the script in the first place. Below is a dumb solution.
docker_sudo=sudo

${docker_sudo} docker pull jupyterhub/singleuser
