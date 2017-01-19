#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

FF_APP_NAME_DEFAULT="app"
FF_IMAGE_NAME_DEFAULT="featurefactory"
FF_DATA_DIR_DEFAULT="/var/lib/featurefactory"
JUPYTERHUB_CONFIG_DIR_DEFAULT="/etc/featurefactory"
MYSQL_CONTAINER_NAME_DEFAULT="featurefactorymysql"
MYSQL_ADMIN_USERNAME_DEFAULT="admin"
MYSQL_ADMIN_USERNAME_PASSWORD_DEFAULT="admin"

# ------------------------------------------------------------------------------
# Read user input

echo -n "Enter FeatureFactory app name [default '$FF_APP_NAME_DEFAULT']: "
read FF_APP_NAME
[ "$FF_APP_NAME" = "" ] && FF_APP_NAME=$FF_APP_NAME_DEFAULT

echo -n "Enter FeatureFactory docker image name [default '$FF_IMAGE_NAME_DEFAULT']: "
read FF_IMAGE_NAME
[ "$FF_IMAGE_NAME" = "" ] && FF_IMAGE_NAME=$FF_IMAGE_NAME_DEFAULT

echo -n "Enter FeatureFactory data directory [default '$FF_DATA_DIR_DEFAULT']: "
read FF_DATA_DIR
[ "$FF_DATA_DIR" = "" ] && FF_DATA_DIR=$FF_DATA_DIR_DEFAULT

echo -n "Enter jupyterhub config directory [default '$JUPYTERHUB_CONFIG_DIR_DEFAULT']: "
read JUPYTERHUB_CONFIG_DIR
[ "$JUPYTERHUB_CONFIG_DIR" = "" ] && JUPYTERHUB_CONFIG_DIR=$JUPYTERHUB_CONFIG_DIR_DEFAULT

echo -n "Enter FeatureFactory MySQL docker container name [default '$MYSQL_CONTAINER_NAME_DEFAULT']: "
read MYSQL_CONTAINER_NAME
[ "$MYSQL_CONTAINER_NAME" = "" ] && MYSQL_CONTAINER_NAME=$MYSQL_CONTAINER_NAME_DEFAULT

echo -n "Enter FeatureFactory MySQL admin username [default '$MYSQL_ADMIN_USERNAME_DEFAULT']: "
read MYSQL_ADMIN_USERNAME
[ "$MYSQL_ADMIN_USERNAME" = "" ] && MYSQL_ADMIN_USERNAME=$MYSQL_ADMIN_USERNAME_DEFAULT

echo -n "Enter FeatureFactory MySQL admin password [default '$MYSQL_ADMIN_USERNAME_PASSWORD_DEFAULT']: "
read MYSQL_ADMIN_USERNAME_PASSWORD
[ "$MYSQL_ADMIN_USERNAME_PASSWORD" = "" ] && MYSQL_ADMIN_USERNAME_PASSWORD=$MYSQL_ADMIN_USERNAME_PASSWORD_DEFAULT

# ------------------------------------------------------------------------------
# Some brief validation

if [ ! -d "$JUPYTERHUB_CONFIG_DIR" ]; then
    sudo mkdir -p "$JUPYTERHUB_CONFIG_DIR"
fi
if [ ! -d "$FF_DATA_DIR" ]; then
    sudo mkdir -p "$FF_DATA_DIR"
fi

# we must have user-writable config directories
#TODO this solution is sketchy
sudo chown $USER "$JUPYTERHUB_CONFIG_DIR"
sudo chown $USER "$FF_DATA_DIR"

# ------------------------------------------------------------------------------
# Install jupyterhub

${SCRIPT_DIR}/install_jupyterhub.sh \
    "$FF_APP_NAME" \
    "$FF_IMAGE_NAME" \
    "$JUPYTERHUB_CONFIG_DIR" \
    "$MYSQL_CONTAINER_NAME"
