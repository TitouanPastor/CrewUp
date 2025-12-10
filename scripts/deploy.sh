#!/bin/bash

# CrewUp Deployment Script
# Deploy CrewUp to Kubernetes using Helm

set -e

NAMESPACE="crewup"
RELEASE_NAME="crewup"
CHART_PATH="./helm/crewup"
VALUES_FILE="./helm/crewup/values.yaml"

echo "================================================"
echo "  CrewUp Kubernetes Deployment"
echo "================================================"
echo ""

# Check prerequisites
if ! command -v helm &> /dev/null; then
    echo "❌ Error: Helm is not installed"
    echo "Install: https://helm.sh/docs/intro/install/"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo "❌ Error: kubectl is not installed"
    echo "Install: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check cluster connection
echo "🔍 Checking Kubernetes cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Error: Cannot connect to Kubernetes cluster"
    exit 1
fi

CLUSTER=$(kubectl config current-context)
echo "✅ Connected to: $CLUSTER"
echo ""

# Show configuration
echo "Deployment Configuration:"
echo "  Namespace: $NAMESPACE"
echo "  Release: $RELEASE_NAME"
echo "  Chart: $CHART_PATH"
echo ""

# Create namespace
echo "📦 Creating namespace..."
kubectl create namespace $NAMESPACE 2>/dev/null || echo "Namespace already exists"

# Deploy with Helm
echo ""
echo "🚀 Deploying CrewUp..."
helm install $RELEASE_NAME -f $VALUES_FILE -n $NAMESPACE $CHART_PATH

echo ""
echo "================================================"
echo "✅ CrewUp deployed successfully!"
echo "================================================"
echo ""
echo "📋 Useful commands:"
echo "  Check pods:    kubectl get pods -n $NAMESPACE"
echo "  Check services: kubectl get svc -n $NAMESPACE"
echo "  Check all:     kubectl get all -n $NAMESPACE"
echo "  Check ingress:  kubectl get ingress -n $NAMESPACE"
echo "  View logs:     kubectl logs -l app=<service-name> -n $NAMESPACE"
echo ""
echo "🌐 Your application will be available at the domain specified in values.yaml"
echo "   (after DNS propagation and certificate issuance)"
echo ""
