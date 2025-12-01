-- CrewUp PostgreSQL Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS & AUTHENTICATION
-- ============================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keycloak_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    bio TEXT,
    profile_picture_url TEXT,
    interests TEXT[],
    reputation DECIMAL(3, 2) DEFAULT 0.00 CHECK (reputation >= 0 AND reputation <= 5),
    is_active BOOLEAN DEFAULT TRUE,
    is_banned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for faster lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_keycloak_id ON users(keycloak_id);
CREATE INDEX idx_users_reputation ON users(reputation);

-- ============================================
-- REPUTATION SYSTEM
-- ============================================

-- Ratings given to users after events
CREATE TABLE ratings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rated_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rater_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    event_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate ratings for same event and no self-rating
    UNIQUE(rated_user_id, rater_user_id, event_id),
    CHECK (rated_user_id != rater_user_id)
);

CREATE INDEX idx_ratings_rated_user ON ratings(rated_user_id);

-- View to calculate average reputation for each user
CREATE VIEW user_reputation AS
SELECT 
    u.id AS user_id,
    COALESCE(AVG(r.rating), 0) AS average_rating,
    COUNT(r.id) AS total_ratings
FROM users u
LEFT JOIN ratings r ON u.id = r.rated_user_id
GROUP BY u.id;

-- ============================================
-- EVENTS
-- ============================================

CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    creator_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    event_type VARCHAR(50) CHECK (event_type IN ('bar', 'club', 'concert', 'party', 'restaurant', 'outdoor', 'sports', 'other')),
    
    -- Location
    address TEXT NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Date & time
    event_start TIMESTAMP WITH TIME ZONE NOT NULL,
    event_end TIMESTAMP WITH TIME ZONE,
    
    max_attendees INTEGER CHECK (max_attendees > 0),
    is_public BOOLEAN DEFAULT TRUE,
    is_cancelled BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Event must be in the future when created
    CHECK (event_start > created_at),
    CHECK (event_end IS NULL OR event_end > event_start)
);

CREATE INDEX idx_events_start ON events(event_start);
CREATE INDEX idx_events_creator ON events(creator_id);
CREATE INDEX idx_events_location ON events(latitude, longitude);
CREATE INDEX idx_events_type ON events(event_type);

-- Add foreign key to ratings
ALTER TABLE ratings 
ADD CONSTRAINT fk_ratings_event 
FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE;

-- ============================================
-- GROUPS & GROUP MEMBERSHIP
-- ============================================

CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    max_members INTEGER DEFAULT 10 CHECK (max_members > 0),
    is_private BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_groups_event ON groups(event_id);

-- Junction table for users in groups
CREATE TABLE group_members (
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE,
    
    PRIMARY KEY (group_id, user_id)
);

CREATE INDEX idx_group_members_group ON group_members(group_id);
CREATE INDEX idx_group_members_user ON group_members(user_id);

-- ============================================
-- CHAT MESSAGES
-- ============================================

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL CHECK (LENGTH(content) > 0 AND LENGTH(content) <= 2000),
    is_edited BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_group_sent ON messages(group_id, sent_at);

-- ============================================
-- SAFETY / PARTY MODE
-- ============================================

CREATE TABLE safety_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    batch_id UUID,  -- Links alerts sent to multiple groups at once
    
    -- Location at time of alert
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    alert_type VARCHAR(50) DEFAULT 'help' CHECK (alert_type IN ('help', 'medical', 'harassment', 'other')),
    message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_safety_alerts_group ON safety_alerts(group_id);
CREATE INDEX idx_safety_alerts_user ON safety_alerts(user_id);
CREATE INDEX idx_safety_alerts_created ON safety_alerts(created_at);
CREATE INDEX idx_safety_alerts_batch ON safety_alerts(batch_id);

-- ============================================
-- EVENT ATTENDEES (RSVP status)
-- ============================================

CREATE TABLE event_attendees (
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'going' CHECK (status IN ('going', 'interested', 'not_going')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (event_id, user_id)
);

CREATE INDEX idx_event_attendees_user ON event_attendees(user_id);
CREATE INDEX idx_event_attendees_status ON event_attendees(event_id, status);


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