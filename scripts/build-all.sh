#!/bin/bash

# Script to build all Docker containers for CrewUp project
# This script reads service names from docker-compose.yaml and builds each container

echo "Building all CrewUp Docker containers..."
echo "========================================"

# Array of services from docker-compose.yaml
services=("event" "group" "rating" "safety" "user" "frontend")

# Build each service
for service in "${services[@]}"; do
    echo ""
    echo "Building $service service..."
    echo "----------------------------"
    
    if [ -d "./$service" ]; then
        docker build -t "crewup-$service:latest" "./$service"
        
        if [ $? -eq 0 ]; then
            echo "✓ Successfully built crewup-$service"
        else
            echo "✗ Failed to build crewup-$service"
            exit 1
        fi
    else
        echo "✗ Directory ./$service not found"
        exit 1
    fi
done

echo ""
echo "========================================"
echo "All containers built successfully!"
echo ""
echo "You can now run 'docker-compose up' to start the services."
