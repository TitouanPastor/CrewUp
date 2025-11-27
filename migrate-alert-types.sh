#!/bin/bash

# Migration script for safety alert types
# Usage: ./migrate-alert-types.sh [dev|staging|production]

set -e

ENVIRONMENT=${1:-dev}

echo "=========================================="
echo "Safety Alert Types Migration"
echo "Environment: $ENVIRONMENT"
echo "=========================================="

# Get the PostgreSQL pod name for the environment
case "$ENVIRONMENT" in
  dev)
    NAMESPACE="crewup-dev"
    ;;
  staging)
    NAMESPACE="crewup-staging"
    ;;
  production)
    NAMESPACE="crewup-production"
    ;;
  *)
    echo "❌ Invalid environment. Use: dev, staging, or production"
    exit 1
    ;;
esac

echo ""
echo "📋 Checking current constraint..."
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c "\d safety_alerts" | grep -A 2 "Check constraints"

echo ""
echo "⚠️  About to update alert_type constraint in $ENVIRONMENT"
echo "   Old values: help, emergency, other"
echo "   New values: help, medical, harassment, other"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Migration cancelled"
    exit 0
fi

echo ""
echo "🔄 Applying migration..."

# Apply the migration - drop old constraint
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c "ALTER TABLE safety_alerts DROP CONSTRAINT IF EXISTS safety_alerts_alert_type_check;"

# Add new constraint
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c "ALTER TABLE safety_alerts ADD CONSTRAINT safety_alerts_alert_type_check CHECK (alert_type IN ('help', 'medical', 'harassment', 'other'));"

echo ""
echo "✅ Migration completed successfully!"
echo ""
echo "📊 Checking for any existing 'emergency' alerts (if any, they need manual update)..."
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c "SELECT COUNT(*) as emergency_alerts FROM safety_alerts WHERE alert_type = 'emergency';"

echo ""
echo "ℹ️  If emergency_alerts > 0, run this to convert them:"
echo "   kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c \"UPDATE safety_alerts SET alert_type = 'medical' WHERE alert_type = 'emergency';\""
