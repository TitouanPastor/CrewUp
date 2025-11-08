#!/bin/bash

# CrewUp Upgrade Script
# Update an existing CrewUp deployment

set -e

NAMESPACE="crewup"
RELEASE_NAME="crewup"
CHART_PATH="./helm/crewup"
VALUES_FILE="./helm/crewup/values.yaml"

echo "================================================"
echo "  CrewUp Upgrade"
echo "================================================"
echo ""

# Check if release exists
if ! helm list -n $NAMESPACE | grep -q $RELEASE_NAME; then
    echo "❌ Error: Release '$RELEASE_NAME' not found in namespace '$NAMESPACE'"
    echo "Run ./deploy.sh to install first"
    exit 1
fi

echo "Current deployment:"
helm list -n $NAMESPACE | grep $RELEASE_NAME
echo ""

read -p "Proceed with upgrade? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Upgrade cancelled"
    exit 0
fi

echo ""
echo "📦 Upgrading CrewUp..."
helm upgrade $RELEASE_NAME -f $VALUES_FILE -n $NAMESPACE $CHART_PATH

echo ""
echo "✅ CrewUp upgraded successfully!"
echo ""
echo "📋 Check rollout status:"
echo "  kubectl rollout status deployment -n $NAMESPACE"
echo ""
