#!/usr/bin/env bash

# Generate SSL certificate
set -e

source .env
source .env.local >/dev/null 2>&1 || true

echo "Generating SSL certificate..."

./letsencrypt.sh \
    --email ${FF_DOMAIN_EMAIL} \
    --domain ${FF_DOMAIN_NAME} \
    --volume ${SECRETS_VOLUME_NAME}

echo "Generating SSL certificate...done"
