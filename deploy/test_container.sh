#!/usr/bin/env bash

set -x

apt-get update
apt-get install sudo

# From http://www.yegor256.com/2014/08/29/docker-non-root.html
TESTUSER=r
adduser --disabled-password --gecos '' $TESTUSER
adduser $TESTUSER sudo
echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

TEMPDIR=$(mktemp -d)
cp /tmp/deploy/* $TEMPDIR
chown -R $TESTUSER:$TESTUSER $TEMPDIR

# Run build script. We run as login shell to ensure that typical environment
# variables, which are expected in the build process, are available.
su --login $TESTUSER -c $TEMPDIR/build.sh
