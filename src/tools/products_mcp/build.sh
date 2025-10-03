#!/bin/bash
# Build script for Products MCP Server Docker image

set -e

# Configuration
IMAGE_NAME="products-mcp"
VERSION="${1:-latest}"

echo "================================================"
echo "Building Products MCP Server Docker Image"
echo "================================================"
echo "Image: ${IMAGE_NAME}:${VERSION}"
echo ""

# Build the image
echo "Building Docker image..."
docker build -t "${IMAGE_NAME}:${VERSION}" .

echo ""
echo "✅ Build complete!"
echo ""
echo "Run locally:"
echo "  docker run --rm --env-file .env ${IMAGE_NAME}:${VERSION}"
echo ""
echo "Tag for ACR:"
echo "  docker tag ${IMAGE_NAME}:${VERSION} <your-acr>.azurecr.io/${IMAGE_NAME}:${VERSION}"
echo ""
