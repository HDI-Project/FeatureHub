#!/usr/bin/env bash

# Generate SSL certificate

source .env

echo "Generating SSL certificate..."

if [ ! -d "$FF_DATA_DIR/config" ]; then
    mkdir -p "$FF_DATA_DIR/config"
fi

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$FF_DATA_DIR/config/jupyterhub/key.pem" \
    -out "$FF_DATA_DIR/config/jupyterhub/cert.pem" \
    -batch

echo "Generating SSL certificate...done"
