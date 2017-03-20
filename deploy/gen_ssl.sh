#!/usr/bin/env bash

# Generate SSL certificate
set -e

source .env
source .env.local >/dev/null 2>&1 || true

echo "Generating SSL certificate..."

# Check USE_LETSENCRYPT_CERT to determine if we use Lets Encrypt or generate a
# self-signed certificate.
# If variable is *unset* or *set and NOT falsy* (does not match falsy regex), then use
# letsencrypt.
falsy='^(no?|f(alse)?|off|0)$'
if [[ -z ${USE_LETSENCRYPT_CERT+x} ]] || \
    ! $(echo "${USE_LETSENCRYPT_CERT}" | grep -q -i -E $falsy);
then
    echo "Using Lets Encrypt-signed certificate..."
    ./letsencrypt.sh \
        --email ${FF_DOMAIN_EMAIL} \
        --domain ${FF_DOMAIN_NAME} \
        --volume ${SECRETS_VOLUME_NAME}
else
    echo "Using self-signed certificate..."
    docker run -i --rm \
        -v "${SECRETS_VOLUME_NAME}:/etc/letsencrypt" \
        --entrypoint=/bin/bash \
        quay.io/letsencrypt/letsencrypt:latest <<EOF
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "/etc/letsencrypt/privkey.pem" \
    -out "/etc/letsencrypt/cert.pem" \
    -batch
EOF
fi

echo "Generating SSL certificate...done"
