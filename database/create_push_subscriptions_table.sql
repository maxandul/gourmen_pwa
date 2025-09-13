-- Push Subscriptions Tabelle für echte Push-Benachrichtigungen
-- Führe dieses SQL auf Railway aus

CREATE TABLE push_subscriptions (
    id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL,
    endpoint TEXT NOT NULL,
    p256dh_key TEXT NOT NULL,
    auth_key TEXT NOT NULL,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_used_at TIMESTAMP,
    
    -- Foreign Key Constraint
    CONSTRAINT fk_push_subscriptions_member 
        FOREIGN KEY (member_id) 
        REFERENCES members(id) 
        ON DELETE CASCADE,
    
    -- Indexes für Performance
    INDEX idx_push_subscriptions_member_id (member_id),
    INDEX idx_push_subscriptions_endpoint (endpoint),
    INDEX idx_push_subscriptions_active (is_active),
    INDEX idx_push_subscriptions_last_used (last_used_at)
);

-- Trigger für updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_push_subscriptions_updated_at 
    BEFORE UPDATE ON push_subscriptions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
