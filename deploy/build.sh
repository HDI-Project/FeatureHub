#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e
set -x

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function die {
    echo "Error: $1"
    exit 1
}

FF_APP_NAME_DEFAULT="app"
FF_IMAGE_NAME_DEFAULT="featurefactory"
FF_DATA_DIR_DEFAULT="/var/lib/featurefactory"
JUPYTERHUB_CONFIG_DIR_DEFAULT="/etc/featurefactory"
MYSQL_CONTAINER_NAME_DEFAULT="featurefactorymysql"
MYSQL_DATABASE_NAME_DEFAULT="featurefactory"
MYSQL_ADMIN_USERNAME_DEFAULT="featurefactoryadmin"
MYSQL_ADMIN_PASSWORD_DEFAULT="featurefactoryadmin"

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

echo -n "Enter FeatureFactory MySQL database name [default '$MYSQL_DATABASE_NAME_DEFAULT']: "
read MYSQL_DATABASE_NAME
[ "$MYSQL_DATABASE_NAME" = "" ] && MYSQL_DATABASE_NAME=$MYSQL_DATABASE_NAME_DEFAULT

echo -n "Enter FeatureFactory MySQL admin username [default '$MYSQL_ADMIN_USERNAME_DEFAULT']: "
read MYSQL_ADMIN_USERNAME
[ "$MYSQL_ADMIN_USERNAME" = "" ] && MYSQL_ADMIN_USERNAME=$MYSQL_ADMIN_USERNAME_DEFAULT

echo -n "Enter FeatureFactory MySQL admin password [default '$MYSQL_ADMIN_PASSWORD_DEFAULT']: "
read MYSQL_ADMIN_PASSWORD
[ "$MYSQL_ADMIN_PASSWORD" = "" ] && MYSQL_ADMIN_PASSWORD=$MYSQL_ADMIN_PASSWORD_DEFAULT

# ------------------------------------------------------------------------------
# Some brief validation

# Detect Debian vs CentOS
PKG_MGR=""
if which apt-get >/dev/null 2>&1; then
    PKG_MGR="apt-get"
elif which yum >/dev/null 2>&1; then
    PKG_MGR="yum"
else
    die "Package manager not found. yum and apt-get are okay. Are you on a Linux system?"
fi
echo "Package manager is $PKG_MGR"
export PKG_MGR

if [ ! -d "$JUPYTERHUB_CONFIG_DIR" ]; then
    sudo mkdir -p "$JUPYTERHUB_CONFIG_DIR"
fi
if [ ! -d "$FF_DATA_DIR" ]; then
    sudo mkdir -p "$FF_DATA_DIR"
fi

# we must have user-writable config directories
#TODO this solution is sketchy
sudo chown -R $USER:$USER "$JUPYTERHUB_CONFIG_DIR"
sudo chmod -R u+w "$JUPYTERHUB_CONFIG_DIR"
sudo chown -R $USER:$USER "$FF_DATA_DIR"
sudo chmod -R u+w "$FF_DATA_DIR"

# ------------------------------------------------------------------------------
# Install and configure application components

# Install jupyterhub
${SCRIPT_DIR}/install_jupyterhub.sh \
    "$FF_APP_NAME" \
    "$FF_IMAGE_NAME" \
    "$JUPYTERHUB_CONFIG_DIR" \
    "$MYSQL_CONTAINER_NAME"

# Install docker
${SCRIPT_DIR}/install_docker.sh

# Install mysql
${SCRIPT_DIR}/install_mysql.sh \
    "$MYSQL_CONTAINER_NAME" \
    "$MYSQL_DATABASE_NAME" \
    "$MYSQL_ADMIN_USERNAME" \
    "$MYSQL_ADMIN_PASSWSORD"

# Create and authenticate a test, non-admin user.
MYSQL_NEWUSER_USERNAME=testuser
MYSQL_NEWUSER_PASSWORD=abc123
${SCRIPT_DIR}/add_user.sh \
    $MYSQL_CONTAINER_NAME \
    $MYSQL_DATABASE_NAME \
    $MYSQL_ADMIN_USERNAME \
    $MYSQL_ADMIN_PASSWORD \
    $MYSQL_NEWUSER_USERNAME \
    $MYSQL_NEWUSER_PASSWORD
