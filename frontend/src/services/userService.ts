import api from './api';

// User types
export interface User {
  id: string;
  keycloak_id: string;
  email: string;
  first_name: string;
  last_name: string;
  bio: string | null;
  profile_picture_url: string | null;
  interests: string[];
  reputation_score: number;
  total_ratings: number;
  created_at: string;
  updated_at: string;
}

export interface PublicUser {
  id: string;
  first_name: string;
  last_name: string;
  bio: string | null;
  profile_picture_url: string | null;
  interests: string[];
  reputation_score: number;
  total_ratings: number;
}

export interface UserUpdate {
  bio?: string;
  interests?: string[];
}

// User Service API
export const userService = {
  /**
   * Create or get current user profile from Keycloak token
   * POST /users - Idempotent (returns 200 if exists, 201 if created)
   */
  createProfile: async (): Promise<User> => {
    const { data } = await api.post<User>('/users');
    return data;
  },

  /**
   * Get current user's full profile
   * GET /users/me
   */
  getMe: async (): Promise<User> => {
    const { data } = await api.get<User>('/users/me');
    return data;
  },

  /**
   * Update current user's profile
   * PUT /users/me
   */
  updateProfile: async (update: UserUpdate): Promise<User> => {
    const { data } = await api.put<User>('/users/me', update);
    return data;
  },

  /**
   * Get public profile of any user by ID
   * GET /users/{id}
   */
  getUserById: async (id: string): Promise<PublicUser> => {
    const { data } = await api.get<PublicUser>(`/users/${id}`);
    return data;
  },

  /**
   * Health check
   * GET /health
   */
  healthCheck: async (): Promise<{ status: string; database: string; timestamp: string }> => {
    const { data } = await api.get('/health');
    return data;
  },
};
