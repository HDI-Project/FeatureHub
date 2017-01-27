#!/usr/bin/env bash

# Run build script.
/tmp/ff/deploy/build.sh -y

# Don't exit application
tail -F -n0 /etc/hosts
