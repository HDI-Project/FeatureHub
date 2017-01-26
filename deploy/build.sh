#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e
set -x

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

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
# Settings

#todo redo defaults
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
    "$JUPYTERHUB_CONFIG_DIR" \
    "$MYSQL_CONTAINER_NAME"

# Finally, create ff image
${SCRIPT_DIR}/create_ff_image.sh \
    $FF_IMAGE_NAME \
    $JUPYTERHUB_CONFIG_DIR \
    $MYSQL_CONTAINER_NAME

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
