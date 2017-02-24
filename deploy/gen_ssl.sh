#!/usr/bin/env bash

# Generate SSL certificate
set -e

source .env

echo "Generating SSL certificate..."

d=$(mktemp -d)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$d/ssl_key.pem" \
    -out "$d/ssl_cert.pem" \
    -batch

# Dumb way of putting secrets into secrets volume
docker run -it --rm \
    -v "${d}:/tmp/ssl" \
    -v "${SECRETS_VOLUME_NAME}:/etc/letsencrypt" \
    busybox mv /tmp/ssl/ssl_key.pem /tmp/ssl/ssl_cert.pem /etc/letsencrypt

echo "Generating SSL certificate...done"
