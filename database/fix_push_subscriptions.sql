-- Fix push_subscriptions table schema
-- Add missing columns if they don't exist

-- Check current table structure
\d push_subscriptions;

-- Add missing columns
ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS created_at DATE;
ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS updated_at DATE;
ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS last_used_at DATE;

-- Fill existing NULL values with current date
UPDATE push_subscriptions SET created_at = CURRENT_DATE WHERE created_at IS NULL;
UPDATE push_subscriptions SET updated_at = CURRENT_DATE WHERE updated_at IS NULL;

-- Add NOT NULL constraints for created_at and updated_at
ALTER TABLE push_subscriptions ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE push_subscriptions ALTER COLUMN updated_at SET NOT NULL;

-- Add default values for future inserts
ALTER TABLE push_subscriptions ALTER COLUMN created_at SET DEFAULT CURRENT_DATE;
ALTER TABLE push_subscriptions ALTER COLUMN updated_at SET DEFAULT CURRENT_DATE;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_member_id ON push_subscriptions (member_id);
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_endpoint ON push_subscriptions (endpoint);
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_active ON push_subscriptions (is_active);
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_last_used ON push_subscriptions (last_used_at);

-- Show final table structure
\d push_subscriptions;

-- Show sample data
SELECT * FROM push_subscriptions LIMIT 5;
