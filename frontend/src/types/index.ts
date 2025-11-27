export interface User {
  id: number | string;  // Support both numeric and UUID from Keycloak
  email: string;
  first_name: string;
  last_name: string;
  bio?: string;
  created_at: string;
  reputation?: {
    average_rating: number;
    total_reviews: number;
  };
}

export interface Event {
  id: string;  // UUID format
  creator_id: string;  // UUID format
  name: string;
  description?: string;
  event_type?: 'bar' | 'club' | 'concert' | 'party' | 'restaurant' | 'outdoor' | 'sports' | 'other';
  address: string;
  latitude?: string | number;
  longitude?: string | number;
  event_start: string;
  event_end?: string;
  max_attendees?: number | null;
  is_public: boolean;
  is_cancelled: boolean;
  created_at: string;
  updated_at: string;

  // Creator details
  creator_first_name?: string;
  creator_last_name?: string;
  creator_profile_picture?: string;

  // Computed fields
  participant_count: number;
  interested_count: number;
  is_full: boolean;
  user_status?: 'going' | 'interested' | 'not_going' | null;
}

export interface EventAttendee {
  user_id: string;  // UUID
  keycloak_id?: string;
  first_name?: string;
  last_name?: string;
  status: 'going' | 'interested' | 'not_going';
  joined_at: string;
}

export interface Group {
  id: string;  // UUID format
  event_id: number;
  name: string;
  max_members: number;
  created_at: string;
  members?: GroupMember[];
  members_count?: number;
}

export interface GroupMember {
  id: number;
  user_id: number;
  group_id: number;
  joined_at: string;
  is_admin: boolean;
  user?: User;
}

export interface Message {
  id: number;
  group_id: number;
  sender_id: number;
  content: string;
  sent_at: string;
  sender?: User;
}

export interface Review {
  id: number;
  reviewed_user_id: number;
  reviewer_user_id: number;
  rating: number;
  comment?: string;
  event_id: number;
  created_at: string;
}

export interface SafetyAlert {
  id: string;
  user_id: string;
  event_id: string;
  group_id: string;
  alert_type: 'help' | 'medical' | 'harassment' | 'other';
  message?: string;
  latitude?: number;
  longitude?: number;
  created_at: string;
  resolved_at?: string;
  resolved: boolean;
  user?: User;
}

export interface EventRSVP {
  status: 'going' | 'interested' | 'not_going';
}
