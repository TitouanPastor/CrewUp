-- Migration: Add is_banned column to users table (idempotent)
-- Date: 2025-12-02
-- Description: Add is_banned flag to support user ban functionality

-- Add is_banned column with default value FALSE
ALTER TABLE users
ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE NOT NULL;

-- Backfill: All existing users are not banned by default (already handled by DEFAULT)
-- No UPDATE needed since DEFAULT FALSE will apply to existing rows
