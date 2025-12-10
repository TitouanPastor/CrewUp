#!/bin/bash

# CrewUp Cleanup Script
# Remove CrewUp from Kubernetes

set -e

NAMESPACE="crewup"

echo "================================================"
echo "  CrewUp Cleanup"
echo "================================================"
echo ""
echo "⚠️  This will delete the namespace '$NAMESPACE' and all resources inside it!"
echo ""
read -p "Are you sure? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled"
    exit 0
fi

echo ""
echo "🗑️  Deleting namespace $NAMESPACE..."
kubectl delete namespace $NAMESPACE

echo ""
echo "✅ CrewUp has been removed successfully!"
echo ""
