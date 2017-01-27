#!/usr/bin/env bash

apt-get update
apt-get install sudo

# From http://www.yegor256.com/2014/08/29/docker-non-root.html
TESTUSER=r
adduser --disabled-password --gecos '' $TESTUSER
adduser $TESTUSER sudo
echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Run build script. We run as login shell to ensure that typical environment
# variables, which are expected in the build process, are available.
su --login $TESTUSER -c "/tmp/ff/deploy/build.sh -y"

# Don't exit application
tail -F -n0 /etc/hosts
