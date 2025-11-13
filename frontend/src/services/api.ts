import axios from 'axios';
import keycloak from '../keycloak';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: add authentication token
api.interceptors.request.use(
  async (config) => {
    // Add Keycloak token to all requests
    if (keycloak.token) {
      config.headers.Authorization = `Bearer ${keycloak.token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: handle common errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Handle 401 Unauthorized: redirect to login
    if (error.response?.status === 401) {
      await keycloak.login();
    }

    // Handle 403 Forbidden: token might be expired, try refresh
    if (error.response?.status === 403) {
      try {
        const refreshed = await keycloak.updateToken(5);
        if (refreshed) {
          // Retry the original request with new token
          error.config.headers.Authorization = `Bearer ${keycloak.token}`;
          return api.request(error.config);
        }
      } catch {
        // Refresh failed, redirect to login
        await keycloak.login();
      }
    }

    return Promise.reject(error);
  }
);

export default api;
