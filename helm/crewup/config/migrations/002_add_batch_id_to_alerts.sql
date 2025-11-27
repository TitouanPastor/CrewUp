-- Migration: Add batch_id to safety_alerts
-- This allows grouping alerts sent to multiple groups at once

ALTER TABLE safety_alerts 
ADD COLUMN batch_id UUID;

-- Create index for batch queries
CREATE INDEX idx_safety_alerts_batch ON safety_alerts(batch_id);

-- Backfill: Generate unique batch_ids for existing alerts
UPDATE safety_alerts 
SET batch_id = id 
WHERE batch_id IS NULL;
