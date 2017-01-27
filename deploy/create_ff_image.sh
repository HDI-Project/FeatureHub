#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# Setup

set -e

if [ "$#" != "3" ]; then
    echo "usage: ./create_ff_image.sh ff_image_name jupyterhub_config_dir"
    echo "                            mysql_container_name"
    exit 1
fi

FF_IMAGE_NAME=$1
JUPYTERHUB_CONFIG_DIR=$2
MYSQL_CONTAINER_NAME=$3

# ------------------------------------------------------------------------------

TEMPDIR=$(mktemp -d)

# Testing: copy the FeatureFactory package into the temporary directory
cp -r /tmp/FeatureFactory_src $TEMPDIR/FeatureFactory

# # Production: Download the FeatureFactory package
# git clone https://github.com/HDI-Project/FeatureFactory $TEMPDIR/FeatureFactory

# Download jupyterhub dockerspawner
git clone https://github.com/jupyterhub/dockerspawner $TEMPDIR/dockerspawner

# Install dockerspawner
pip${PYTHON_VERSION} install requirements -r $TEMPDIR/dockerspawner/requirements.txt
( cd $TEMPDIR/dockerspawner && python${PYTHON_VERSION} setup.py install )

# Populate files needed for image
rm -rf $TEMPDIR/featurefactoryimage
mkdir $TEMPDIR/featurefactoryimage
cp -r $TEMPDIR/FeatureFactory/src \
      $TEMPDIR/FeatureFactory/requirements.txt \
      $TEMPDIR/featurefactoryimage

cat >$TEMPDIR/featurefactoryimage/Dockerfile <<EOF
FROM jupyterhub/systemuser

# Install mysql-related packages
RUN apt-get update && apt-get install -y libmysqlclient-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --egg mysql-connector-python-rf

# Install featurefactory into site-packages
WORKDIR /opt/conda/lib/python3.5/site-packages
COPY src featurefactory
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
WORKDIR featurefactory
RUN python setup.py install

# Same as jupyterhub/systemuser
CMD ["sh", "/srv/singleuser/systemuser.sh"]
EOF

# mysql container name
cat <<EOF >>$JUPYTERHUB_CONFIG_DIR/featurefactory
[mysql]
host = $MYSQL_CONTAINER_NAME
EOF

docker build -t $FF_IMAGE_NAME $TEMPDIR/featurefactoryimage
