#!/bin/bash

# Migration script for is_banned column in users table
# Usage: ./migrate-is-banned.sh [dev|staging|production]

set -e

ENVIRONMENT=${1:-dev}

echo "=========================================="
echo "Users is_banned Column Migration"
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
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c "\d users" | grep is_banned || echo "❌ is_banned column does not exist yet"

echo ""
echo "⚠️  About to add is_banned column to users in $ENVIRONMENT"
echo "   This will:"
echo "   1. Add is_banned BOOLEAN column with DEFAULT FALSE"
echo "   2. Set NOT NULL constraint"
echo "   3. All existing users will have is_banned = FALSE"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Migration cancelled"
    exit 0
fi

echo ""
echo "🔄 Applying migration..."

# Add is_banned column
echo "1️⃣  Adding is_banned column..."
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE NOT NULL;"

echo ""
echo "✅ Migration completed successfully!"
echo ""
echo "📊 Verification:"
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c "SELECT COUNT(*) as total_users, COUNT(*) FILTER (WHERE is_banned = FALSE) as not_banned, COUNT(*) FILTER (WHERE is_banned = TRUE) as banned FROM users;"

echo ""
echo "📋 Updated table structure:"
kubectl exec -n $NAMESPACE statefulset/postgres -- psql -U crewup -d crewup -c "\d users" | grep -A 1 is_banned

echo ""
echo "✨ Done! is_banned column is now available in $ENVIRONMENT"
