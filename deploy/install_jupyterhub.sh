#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function print_usage {
    echo "usage: install_jupyterhub.sh ff_app_name ff_image_name jupyterhub_config_dir mysql_container_name"
    echo
    echo "    ff_app_name             name of the feature factory app name, such"
    echo "                            as \"experiment1\"."
    echo "    ff_image_name           name of the feature factory docker image on"
    echo "                            system"
    echo "    jupyterhub_config_dir   directory to store jupyterhub config files"
    echo
    echo "    mysql_container_name    name of the feature factory mysql container" 
    echo
}

function die {
    echo "Error: $1"
    exit 1
}

function print_usage_and_die {
    print_usage
    die "$1"
}

NODE_VERSION="7"
PYTHON_VERSION="3"

# ------------------------------------------------------------------------------
# App config
if [ "$#" != "4" ]; then
    print_usage_and_die "Invalid number of arguments."
fi

FF_APP_NAME="$1"
FF_IMAGE_NAME="$2"
JUPYTERHUB_CONFIG_DIR="$3"
MYSQL_CONTAINER_NAME="$4"

# ------------------------------------------------------------------------------
# Install dependencies

echo "Installing dependencies..."

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

if [ "$PKG_MGR" = "apt-get" ]; then
    sudo apt-get update
    sudo apt-get dist-upgrade
    sudo apt-get install npm nodejs-legacy git python${PYTHON_VERSION}-pip
elif [ "$PKG_MGR" = "yum" ]; then
    sudo yum update
    sudo yum install git python${PYTHON_VERSION}-pip

    # sketchy!!!!!! untrusted code
    curl --silent --location https://rpm.nodesource.com/setup_${NODE_VERSION}.x | sudo bash -
    sudo yum -y install nodejs
fi

sudo npm install -g configurable-http-proxy
sudo pip3 install jupyterhub

# ------------------------------------------------------------------------------
# Generate SSL certificate

echo "Generating SSL certificate..."

KEY_NAME="featurefactory_${FF_APP_NAME}_key.pem"
CERT_NAME="featurefactory_${FF_APP_NAME}_cert.pem"

TMP_DIR=$(mktemp -d)

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$JUPYTERHUB_CONFIG_DIR/$KEY_NAME" \
    -out "$JUPYTERHUB_CONFIG_DIR/$CERT_NAME" \
    -batch

# ------------------------------------------------------------------------------
# Configure jupyterhub

echo "Configuring jupyterhub..."

if [ ! -f "${JUPYTERHUB_CONFIG_DIR}/jupyterhub_config_generated.py" ]; then
    jupyterhub --generate-config -f "${JUPYTERHUB_CONFIG_DIR}/jupyterhub_config_generated.py"
fi
cp "${SCRIPT_DIR}/jupyterhub_config.py" "${JUPYTERHUB_CONFIG_DIR}"
HUB_IP="$(ip -f inet address show dev eth0 | grep inet | awk '{print $2}' | cut -d '/' -f 1)"
cat >>"${JUPYTERHUB_CONFIG_DIR}/jupyterhub_config.py" <<EOF
# System-specific configuration populated by ${SCRIPT_NAME}.
c.JupyterHub.hub_ip = '$HUB_IP'
c.JupyterHub.ssl_key = '$JUPYTERHUB_CONFIG_DIR/$KEY_NAME'
c.JupyterHub.ssl_cert = '$JUPYTERHUB_CONFIG_DIR/$CERT_NAME'
c.DockerSpawner.links = {'$MYSQL_CONTAINER_NAME':'$MYSQL_CONTAINER_NAME'}
c.SystemUserSpawner.container_image = "$FF_IMAGE_NAME"
EOF

echo "Done."

# ------------------------------------------------------------------------------
# Launch script

echo "Creating jupyterhub launch script..."

cat >"$HOME/ff_${FF_APP_NAME}_jupyterhub_launch.sh" <<EOF
#!/usr/bin/env bash
jupyterhub -f $JUPYTERHUB_CONFIG_DIR/jupyterhub_config.py
EOF
chmod u=rx "$HOME/ff_${FF_APP_NAME}_jupyterhub_launch.sh"
