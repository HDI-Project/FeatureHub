#!/usr/bin/env bash

# Run build script.
/tmp/ff/deploy/build.sh -y

# Run server
/root/ff_app_jupyterhub_launch.sh &

# Stay alive
tail -F -n0 /etc/hosts
