export interface User {
  id: number;
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
  id: number;
  creator_id: number;
  name: string;
  description?: string;
  event_type?: string;
  address: string;
  latitude?: number;
  longitude?: number;
  event_start: string;
  created_at: string;
  attendees_count?: number;
  groups_count?: number;
}

export interface Group {
  id: number;
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
  id: number;
  user_id: number;
  group_id: number;
  latitude?: number;
  longitude?: number;
  alert_type: 'help' | 'emergency' | 'other';
  message?: string;
  created_at: string;
  resolved_at?: string;
  user?: User;
}

export interface EventRSVP {
  id: number;
  event_id: number;
  user_id: number;
  status: 'going' | 'interested' | 'not_going';
  created_at: string;
}
