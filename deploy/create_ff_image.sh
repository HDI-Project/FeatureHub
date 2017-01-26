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
sudo pip${PYTHON_VERSION} install requirements -r $TEMPDIR/dockerspawner/requirements.txt
( cd $TEMPDIR/dockerspawner && sudo python${PYTHON_VERSION} setup.py install )

# Populate files needed for image
rm -rf $TEMPDIR/featurefactoryimage
mkdir $TEMPDIR/featurefactoryimage
cp -r $TEMPDIR/FeatureFactory/src \
      $TEMPDIR/FeatureFactory/requirements.txt \
      $TEMPDIR/dockerspawner/systemuser/systemuser.sh \
      $TEMPDIR/featurefactoryimage

cat >$TEMPDIR/featurefactoryimage/featurefactory.conf <<EOF
[mysql]
host = $MYSQL_CONTAINER_NAME
EOF

cat >$TEMPDIR/featurefactoryimage/Dockerfile <<EOF
FROM jupyterhub/singleuser

USER root
WORKDIR /home
RUN userdel jovyan && rm -rf /home/jovyan
ENV SHELL /bin/bash
RUN apt-get update && apt-get install -y libmysqlclient-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --egg mysql-connector-python-rf

WORKDIR /opt/conda/lib/python3.5/site-packages
COPY src featurefactory
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
WORKDIR featurefactory
RUN python setup.py install

RUN conda uninstall terminado

ADD systemuser.sh /srv/singleuser/systemuser.sh
RUN [ ! -d "$JUPYTERHUB_CONFIG_DIR" ] && mkdir -p "$JUPYTERHUB_CONFIG_DIR"
ADD featurefactory.conf "$JUPYTERHUB_CONFIG_DIR/featurefactory.conf"
RUN USER_ID=65000 USER=systemusertest sh /srv/singleuser/systemuser.sh -h && userdel systemusertest

CMD ["sh", "/srv/singleuser/systemuser.sh"]
EOF

docker_sudo=sudo
${docker_sudo} docker build -t $FF_IMAGE_NAME $TEMPDIR/featurefactoryimage
