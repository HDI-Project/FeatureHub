#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e

export SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function die {
    echo "usage: ./build.sh [-y]"
    echo "  -y  Assume yes (or defaults) to all prompts"
    echo "Error: $1"
    exit 1
}

export yes=""
bad=""
while getopts ":y" opt; do
    case $opt in
        y)
            yes="yes"
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            bad="bad"
            ;;
    esac
done

if [ "$bad" = "bad" ]; then
    die "Invalid options"
fi

# ------------------------------------------------------------------------------
# Versions

export MYSQL_VERSION=5.7
export NODE_VERSION=7
export PYTHON_VERSION=3

# ------------------------------------------------------------------------------
# Settings

#todo redo defaults
#todo remove config directory as an option
declare -a setup=("" "app"                     "Enter FeatureFactory app name" \
                  "" "featurefactory"          "Enter FeatureFactory docker image name" \
                  "" "/var/lib/featurefactory" "Enter FeatureFactory data directory" \
                  "" "/etc/featurefactory"     "Enter jupyterhub config directory" \
                  "" "featurefactorymysql"     "Enter FeatureFactory MySQL docker container name (must be unique)" \
                  "" "featurefactory"          "Enter FeatureFactory MySQL database name" \
                  "" "featurefactoryadmin"     "Enter FeatureFactory MySQL admin username" \
                  "" "featurefactoryadmin"     "Enter FeatureFactory MySQL admin password" );

function read_user_input {
    i=$1
    def=${setup[$(( (i-1)*3+2-1 )) ]}
    prompt=${setup[$(( (i-1)*3+3-1 )) ]}
    if [ "$yes" = "yes" ]; then
        x=$def
    else
        echo -n "$prompt [default '$def']: "
        read x
        [ "$x" = "" ] && x=$def
    fi

    setup[$(( (i-1)*3+1-1 ))]=$x
}

n_setup=$(( ${#setup[@]} / 3))
for j in $(seq 1 $n_setup)
do
    read_user_input $j
done

i=1
FF_APP_NAME="${setup[ $(( (i-1)*3+1-1 )) ]}"; i=$((i+1))
FF_IMAGE_NAME="${setup[ $(( (i-1)*3+1-1 )) ]}"; i=$((i+1))
FF_DATA_DIR="${setup[ $(( (i-1)*3+1-1 )) ]}"; i=$((i+1))
JUPYTERHUB_CONFIG_DIR="${setup[ $(( (i-1)*3+1-1 )) ]}"; i=$((i+1))
MYSQL_CONTAINER_NAME="${setup[ $(( (i-1)*3+1-1 )) ]}"; i=$((i+1))
MYSQL_DATABASE_NAME="${setup[ $(( (i-1)*3+1-1 )) ]}"; i=$((i+1))
MYSQL_ADMIN_USERNAME="${setup[ $(( (i-1)*3+1-1 )) ]}"; i=$((i+1))
MYSQL_ADMIN_PASSWORD="${setup[ $(( (i-1)*3+1-1 )) ]}"; i=$((i+1))

# ------------------------------------------------------------------------------
# Some brief validation

# Detect Debian vs CentOS
export PKG_MGR=""
if which apt-get >/dev/null 2>&1; then
    PKG_MGR="apt-get"
elif which yum >/dev/null 2>&1; then
    PKG_MGR="yum"
else
    die "Package manager not found. yum and apt-get are okay. Which system are you on anyway?"
fi
echo "Package manager is $PKG_MGR"

if [ ! -d "$JUPYTERHUB_CONFIG_DIR" ]; then
    mkdir -p "$JUPYTERHUB_CONFIG_DIR"
fi
if [ ! -d "$FF_DATA_DIR" ]; then
    mkdir -p "$FF_DATA_DIR"
fi

# we must have user-writable config directories
#TODO this solution is sketchy
chown -R $USER:$USER "$JUPYTERHUB_CONFIG_DIR"
chmod -R u+w "$JUPYTERHUB_CONFIG_DIR"
chown -R $USER:$USER "$FF_DATA_DIR"
chmod -R u+w "$FF_DATA_DIR"

# Check MYSQL container does not exist. If does exist, rename. Hope this doesn't mess
# anything else up.
if [ "$(docker ps -a -f name=^/${MYSQL_CONTAINER_NAME}$ | wc -l)" != "2" ]; then
    echo "Container ${MYSQL_CONTAINER_NAME} already exists."
    suffix="-$(cat /dev/urandom | tr -dc 'a-f0-9' | fold -w 8 | head -n 1)"
    MYSQL_CONTAINER_NAME="${MYSQL_CONTAINER_NAME}${suffix}"
    echo -n "Create container ${MYSQL_CONTAINER_NAME} instead? [y/N] "
    if [ "$yes" = "yes" ]; then
        echo
    else
        read x
        if [ "$x" != "y" ]; then
            "Exiting..."
            exit 1
        fi
    fi
fi

# ------------------------------------------------------------------------------
# Install and configure application components

# Install some dependencies for multiple components
echo "Installing general dependencies..."
if [ "$PKG_MGR" = "apt-get" ]; then
    apt-get -y update
    apt-get -y dist-upgrade
elif [ "$PKG_MGR" = "yum" ]; then
    yum -y upgrade yum kernel
    yum -y update
fi
${PKG_MGR} -y install git python${PYTHON_VERSION}-pip

# Install docker
${SCRIPT_DIR}/install_docker.sh

# Install mysql
${SCRIPT_DIR}/install_mysql.sh \
    "$MYSQL_CONTAINER_NAME" \
    "$MYSQL_DATABASE_NAME" \
    "$MYSQL_ADMIN_USERNAME" \
    "$MYSQL_ADMIN_PASSWORD"

# Install jupyterhub
${SCRIPT_DIR}/install_jupyterhub.sh \
    "$FF_APP_NAME" \
    "$FF_IMAGE_NAME" \
    "$FF_DATA_DIR" \
    "$JUPYTERHUB_CONFIG_DIR" \
    "$MYSQL_CONTAINER_NAME"

# Finally, create ff image
${SCRIPT_DIR}/create_ff_image.sh \
    $FF_IMAGE_NAME \
    $JUPYTERHUB_CONFIG_DIR \
    $MYSQL_CONTAINER_NAME

# Create and authenticate a test, non-admin user.
FF_NEWUSER_USERNAME=testuser
FF_NEWUSER_PASSWORD=abc123
${SCRIPT_DIR}/add_user.sh \
    $MYSQL_CONTAINER_NAME \
    $MYSQL_DATABASE_NAME \
    $MYSQL_ADMIN_USERNAME \
    $MYSQL_ADMIN_PASSWORD \
    $FF_NEWUSER_USERNAME \
    $FF_NEWUSER_PASSWORD \
    $FF_DATA_DIR
