import api from './api';

// Moderation types
export interface BanUserRequest {
  user_keycloak_id: string;
  ban: boolean;
  reason: string;
}

export interface BanUserResponse {
  success: boolean;
  message: string;
  moderation_action_id: number | null;
}

export interface SearchUsersResponse {
  users: Array<{
    id: string;
    keycloak_id: string;
    email: string;
    first_name: string;
    last_name: string;
    is_banned: boolean;
    is_active: boolean;
  }>;
  total: number;
}

// Moderation Service API
export const moderationService = {
  /**
   * Search for users by name or email
   * GET /users/search?query=...
   */
  searchUsers: async (query: string): Promise<SearchUsersResponse> => {
    const { data } = await api.get<SearchUsersResponse>('/users/search', {
      params: { query },
    });
    return data;
  },

  /**
   * Ban or unban a user
   * POST /moderation/ban
   */
  banUser: async (request: BanUserRequest): Promise<BanUserResponse> => {
    const { data } = await api.post<BanUserResponse>('/moderation/ban', request);
    return data;
  },
};
