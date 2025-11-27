-- Migration: Update safety alert types
-- Date: 2025-11-27
-- Description: Replace 'emergency' with 'medical' and 'harassment' alert types

-- Step 1: Drop the old constraint
ALTER TABLE safety_alerts DROP CONSTRAINT IF EXISTS safety_alerts_alert_type_check;

-- Step 2: Add the new constraint with updated values
ALTER TABLE safety_alerts 
ADD CONSTRAINT safety_alerts_alert_type_check 
CHECK (alert_type IN ('help', 'medical', 'harassment', 'other'));

-- Note: Any existing 'emergency' alerts will need to be manually updated if they exist
-- Example: UPDATE safety_alerts SET alert_type = 'medical' WHERE alert_type = 'emergency';
