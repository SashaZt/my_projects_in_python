#!/bin/bash
set -e

echo "Generating self-signed SSL certificates..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/key.pem \
    -out /etc/ssl/private/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"

echo "SSL certificates generated successfully"