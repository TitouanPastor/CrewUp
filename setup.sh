#!/bin/bash

echo "🚀 CrewUp - Quick Start Script"
echo "================================"
echo ""

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

echo " Building Docker containers..."
echo "This might take a few minutes on first run..."
echo ""

docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo ""
echo "✅ All containers built successfully!"
echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the application, run:"
echo "  docker-compose up"
echo ""
echo "Then open your browser at:"
echo "  🌐 http://localhost:3000"
echo ""
echo "To stop the application:"
echo "  docker-compose down"
echo ""
