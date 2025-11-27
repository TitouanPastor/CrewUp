import api from './api';
import type { Event, EventAttendee } from '../types';

// Request/Response Types
export interface CreateEventData {
  name: string;
  description?: string;
  event_type?: 'bar' | 'club' | 'concert' | 'party' | 'restaurant' | 'outdoor' | 'sports' | 'other';
  address: string;
  latitude?: number | string;
  longitude?: number | string;
  event_start: string;  // ISO 8601 datetime with timezone
  event_end: string;  // ISO 8601 datetime with timezone
  max_attendees?: number | null;
  is_public?: boolean;
}

export interface UpdateEventData {
  name?: string;
  description?: string;
  event_type?: 'bar' | 'club' | 'concert' | 'party' | 'restaurant' | 'outdoor' | 'sports' | 'other';
  address?: string;
  latitude?: number | string;
  longitude?: number | string;
  event_start?: string;
  event_end?: string;
  max_attendees?: number | null;
  is_public?: boolean;
  is_cancelled?: boolean;
}

export interface ListEventsParams {
  event_type?: string;
  is_public?: boolean;
  creator_id?: string;
  start_date_from?: string;
  start_date_to?: string;
  is_cancelled?: boolean;
  status?: 'going' | 'interested' | 'not_going';  // Filter by user's RSVP status
  latitude?: number;
  longitude?: number;
  radius_km?: number;
  include_past?: boolean;  // Include finished events (default: false)
  include_ongoing?: boolean;  // Include ongoing events (default: true)
  limit?: number;
  offset?: number;
}

export interface EventListResponse {
  events: Event[];
  total: number;
  limit: number;
  offset: number;
}

export interface AttendeeListResponse {
  event_id: string;
  total_participants: number;
  going_count: number;
  interested_count: number;
  attendees?: EventAttendee[];
}

export interface GetParticipantsParams {
  status?: 'going' | 'interested' | 'not_going';
  include_details?: boolean;
  limit?: number;
  offset?: number;
}

// Event Service
export const eventService = {
  /**
   * Create a new event.
   * Requires authentication. The authenticated user becomes the event creator.
   */
  async createEvent(data: CreateEventData): Promise<Event> {
    const response = await api.post<Event>('/events', data);
    return response.data;
  },

  /**
   * Get event details by ID.
   * Authentication optional - public events can be viewed by anyone.
   */
  async getEvent(eventId: string): Promise<Event> {
    const response = await api.get<Event>(`/events/${eventId}`);
    return response.data;
  },

  /**
   * Update an event.
   * Only the event creator can update an event.
   * Use PATCH for partial updates or PUT for full updates.
   */
  async updateEvent(eventId: string, data: UpdateEventData): Promise<Event> {
    const response = await api.patch<Event>(`/events/${eventId}`, data);
    return response.data;
  },

  /**
   * Delete (cancel) an event.
   * Only the event creator can delete an event.
   * This marks the event as cancelled (soft delete).
   */
  async deleteEvent(eventId: string): Promise<void> {
    await api.delete(`/events/${eventId}`);
  },

  /**
   * List events with optional filters and pagination.
   * Authentication optional - without auth, only public events are shown.
   */
  async listEvents(params?: ListEventsParams): Promise<EventListResponse> {
    const queryParams = new URLSearchParams();

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }

    const url = `/events${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await api.get<EventListResponse>(url);
    return response.data;
  },

  /**
   * Join an event (RSVP).
   * Requires authentication.
   * Status can be 'going', 'interested', or 'not_going'.
   * Updating an existing RSVP will change the status.
   */
  async joinEvent(eventId: string, status: 'going' | 'interested' | 'not_going' = 'going'): Promise<void> {
    await api.post(`/events/${eventId}/join`, { status });
  },

  /**
   * Leave an event (remove RSVP).
   * Requires authentication.
   * Removes the user's attendance record for this event.
   */
  async leaveEvent(eventId: string): Promise<void> {
    await api.delete(`/events/${eventId}/leave`);
  },

  /**
   * Get event participants.
   * Requires authentication.
   * Returns participant counts and optionally the full list of participants.
   */
  async getParticipants(eventId: string, params?: GetParticipantsParams): Promise<AttendeeListResponse> {
    const queryParams = new URLSearchParams();

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }

    const url = `/events/${eventId}/participants${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await api.get<AttendeeListResponse>(url);
    return response.data;
  },
};
