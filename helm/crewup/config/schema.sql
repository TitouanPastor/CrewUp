-- CrewUp PostgreSQL Database Schema

-- ============================================
-- USERS & AUTHENTICATION
-- ============================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster email lookups during login
CREATE INDEX idx_users_email ON users(email);

-- ============================================
-- REPUTATION SYSTEM
-- ============================================

-- Reviews/Ratings given to users after events
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    reviewed_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reviewer_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT, -- Optional comment
    event_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate reviews for same event
    UNIQUE(reviewed_user_id, reviewer_user_id, event_id)
);

CREATE INDEX idx_reviews_reviewed_user ON reviews(reviewed_user_id);

-- View to calculate average reputation for each user
CREATE VIEW user_reputation AS
SELECT 
    u.id AS user_id,
    COALESCE(AVG(r.rating), 0) AS average_rating,
    COUNT(r.id) AS total_reviews
FROM users u
LEFT JOIN reviews r ON u.id = r.reviewed_user_id
GROUP BY u.id;

-- ============================================
-- EVENTS
-- ============================================

CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    creator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    event_type VARCHAR(50), -- e.g., 'bar', 'club', 'concert', 'party'
    
    -- Location
    address TEXT NOT NULL,
    latitude DECIMAL(10, 8), -- Allows precise GPS coordinates
    longitude DECIMAL(11, 8),
    
    -- Combined date & time for the event
    event_start TIMESTAMP WITH TIME ZONE NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_start ON events(event_start);
CREATE INDEX idx_events_creator ON events(creator_id);
CREATE INDEX idx_events_location ON events(latitude, longitude); -- For geo queries

-- Now add the foreign key to reviews that we couldn't add before
ALTER TABLE reviews 
ADD CONSTRAINT fk_reviews_event 
FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE;

-- ============================================
-- GROUPS & GROUP MEMBERSHIP
-- ============================================

CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    max_members INTEGER DEFAULT 10, -- Limit group size
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_groups_event ON groups(event_id);

-- Junction table for users in groups
CREATE TABLE group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE, -- Group creator/admin
    
    -- Each user can only join a group once
    UNIQUE(group_id, user_id)
);

CREATE INDEX idx_group_members_group ON group_members(group_id);
CREATE INDEX idx_group_members_user ON group_members(user_id);

-- ============================================
-- CHAT MESSAGES
-- ============================================

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_group ON messages(group_id);
CREATE INDEX idx_messages_sent_at ON messages(sent_at);

-- ============================================
-- SAFETY / PARTY MODE
-- ============================================

CREATE TABLE safety_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    
    -- Location at time of alert
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    alert_type VARCHAR(50) DEFAULT 'help' CHECK (alert_type IN ('help', 'emergency', 'other')),
    message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP -- NULL if still active
);

CREATE INDEX idx_safety_alerts_group ON safety_alerts(group_id);
CREATE INDEX idx_safety_alerts_user ON safety_alerts(user_id);
CREATE INDEX idx_safety_alerts_created ON safety_alerts(created_at);

-- ============================================
-- EVENT RSVPS (Going status)
-- ============================================

CREATE TABLE event_rsvps (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'going' CHECK (status IN ('going', 'interested', 'not_going')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Each user can only RSVP once per event
    UNIQUE(event_id, user_id)
);

CREATE INDEX idx_event_rsvps_event ON event_rsvps(event_id);
CREATE INDEX idx_event_rsvps_user ON event_rsvps(user_id);


-- ============================================
-- Triggers and Functions to update timestamps
-- ============================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_events_updated
BEFORE UPDATE ON events
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();