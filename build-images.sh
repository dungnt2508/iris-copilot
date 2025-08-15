#!/bin/bash

# IRIS Backend & Plugin Docker Build Script
echo "🐳 Building IRIS Docker Images..."

# Build Backend API Image
echo "📦 Building Backend API Image..."
docker build -t iris-backend:latest .

if [ $? -eq 0 ]; then
    echo "✅ Backend API Image built successfully!"
else
    echo "❌ Backend API Image build failed!"
    exit 1
fi

# Build Plugin API Image
echo "📦 Building Plugin API Image..."
docker build -t iris-copilot-plugin:latest ./copilot-plugin

if [ $? -eq 0 ]; then
    echo "✅ Plugin API Image built successfully!"
else
    echo "❌ Plugin API Image build failed!"
    exit 1
fi

# List built images
echo "📋 Built Images:"
docker images | grep iris

echo "🎉 All images built successfully!"
echo ""
echo "🚀 To run with Docker Compose:"
echo "   docker-compose up -d"
echo ""
echo "🚀 To run plugin only:"
echo "   cd copilot-plugin && docker-compose up -d"
