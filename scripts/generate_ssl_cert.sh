#!/bin/bash

# Generate self-signed SSL certificates for development

set -e

echo "🔐 Generating SSL certificates for development..."

# Create ssl directory
mkdir -p ssl

# Generate private key
echo "📝 Generating private key..."
openssl genrsa -out ssl/key.pem 2048

# Generate certificate
echo "📜 Generating certificate..."
openssl req -new -x509 -key ssl/key.pem -out ssl/cert.pem -days 365 -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Set permissions
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem

echo "✅ SSL certificates generated successfully!"
echo "   Private key: ssl/key.pem"
echo "   Certificate: ssl/cert.pem"
echo ""
echo "⚠️ These are self-signed certificates for development only."
echo "   For production, use certificates from a trusted CA."
