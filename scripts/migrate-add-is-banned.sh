#!/bin/bash

# Migration script to add is_banned column to users table
# Usage: ./migrate-add-is-banned.sh [staging|production]

set -e

ENVIRONMENT=${1:-staging}

echo "=========================================="
echo "Add is_banned Column Migration"
echo "Environment: $ENVIRONMENT"
echo "=========================================="

# Get the namespace for the environment
case "$ENVIRONMENT" in
  staging)
    NAMESPACE="crewup-staging"
    ;;
  production)
    NAMESPACE="crewup-production"
    ;;
  *)
    echo "❌ Invalid environment. Use: staging or production"
    exit 1
    ;;
esac

echo ""
echo "📋 Checking if is_banned column already exists..."
COLUMN_EXISTS=$(kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -tAc \
    "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='users' AND column_name='is_banned';")

if [ "$COLUMN_EXISTS" -eq "1" ]; then
    echo "✅ Column is_banned already exists in $ENVIRONMENT, skipping migration"
    exit 0
fi

echo ""
echo "⚠️  About to add is_banned column to users table in $ENVIRONMENT"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Migration cancelled"
    exit 0
fi

echo ""
echo "🔄 Applying migration 003_add_is_banned_to_users.sql..."

# Apply the migration
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c \
    "ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT FALSE NOT NULL;"

echo ""
echo "✅ Migration completed successfully!"

# Verify
echo ""
echo "🔍 Verifying column was added..."
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c \
    "SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name='users' AND column_name='is_banned';"

echo ""
echo "✨ Done! The is_banned column has been added to the users table in $ENVIRONMENT."
