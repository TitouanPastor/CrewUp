#!/bin/bash

# Migration script for batch_id column in safety_alerts table
# Usage: ./migrate-batch-id.sh [dev|staging|production]

set -e

ENVIRONMENT=${1:-dev}

echo "=========================================="
echo "Safety Alerts batch_id Migration"
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
echo "📋 Checking current table structure..."
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c "\d safety_alerts" | grep batch_id || echo "❌ batch_id column does not exist yet"

echo ""
echo "⚠️  About to add batch_id column to safety_alerts in $ENVIRONMENT"
echo "   This will:"
echo "   1. Add batch_id UUID column"
echo "   2. Create index on batch_id"
echo "   3. Set existing alerts batch_id = alert id"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Migration cancelled"
    exit 0
fi

echo ""
echo "🔄 Applying migration..."

# Step 1: Add batch_id column
echo "1️⃣  Adding batch_id column..."
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c "ALTER TABLE safety_alerts ADD COLUMN IF NOT EXISTS batch_id UUID;"

# Step 2: Create index
echo "2️⃣  Creating index on batch_id..."
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c "CREATE INDEX IF NOT EXISTS idx_safety_alerts_batch ON safety_alerts(batch_id);"

# Step 3: Update existing rows
echo "3️⃣  Setting batch_id for existing alerts..."
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c "UPDATE safety_alerts SET batch_id = id WHERE batch_id IS NULL;"

echo ""
echo "✅ Migration completed successfully!"
echo ""
echo "📊 Verification:"
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c "SELECT COUNT(*) as total_alerts, COUNT(batch_id) as alerts_with_batch_id FROM safety_alerts;"

echo ""
echo "📋 Updated table structure:"
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c "\d safety_alerts" | grep -A 1 batch_id

echo ""
echo "✨ Done! batch_id column is now available in $ENVIRONMENT"
