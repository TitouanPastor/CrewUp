import api from './api';

// Types
export interface SafetyAlert {
  id: string;
  user_id: string;
  user_name?: string; // Full name of the user who created the alert
  event_id?: string; // Optional since it can be inferred from group
  group_id: string;
  batch_id?: string;  // Links multiple alerts together
  alert_type: 'help' | 'medical' | 'harassment' | 'other';
  message?: string;
  latitude?: number;
  longitude?: number;
  created_at: string;
  resolved_at?: string;
  resolved: boolean;
}

export interface CreateAlertData {
  event_id: string;
  group_id: string;
  batch_id?: string;  // Optional: link multiple alerts together
  alert_type: 'help' | 'medical' | 'harassment' | 'other';
  message?: string;
  latitude?: number;
  longitude?: number;
}

export interface ListAlertsParams {
  group_id?: string;
  event_id?: string;
  resolved?: boolean;
  limit?: number;
  offset?: number;
}

export interface AlertListResponse {
  alerts: SafetyAlert[];
  total: number;
}

// Safety Service
export const safetyService = {
  /**
   * Create a new safety alert
   * Sends alert to all members of the specified group
   */
  async createAlert(data: CreateAlertData): Promise<SafetyAlert> {
    const response = await api.post<SafetyAlert>('/safety', data);
    return response.data;
  },

  /**
   * List safety alerts for a group or event
   */
  async listAlerts(params?: ListAlertsParams): Promise<AlertListResponse> {
    const response = await api.get<AlertListResponse>('/safety', { params });
    return response.data;
  },

  /**
   * Get current user's own alerts
   */
  async getMyAlerts(params?: { resolved?: boolean; limit?: number; offset?: number }): Promise<AlertListResponse> {
    const response = await api.get<AlertListResponse>('/safety/my-alerts', { params });
    return response.data;
  },

  /**
   * Mark an alert as resolved
   */
  async resolveAlert(alertId: string): Promise<SafetyAlert> {
    const response = await api.patch<SafetyAlert>(`/safety/${alertId}/resolve`, {
      resolved: true,
    });
    return response.data;
  },

  /**
   * Get user's current location using browser Geolocation API
   * Returns null if permission denied or unavailable
   */
  async getCurrentLocation(): Promise<{ latitude: number; longitude: number } | null> {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve(null);
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
        },
        () => {
          // Permission denied or error - return null
          resolve(null);
        },
        {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 0,
        }
      );
    });
  },
};
