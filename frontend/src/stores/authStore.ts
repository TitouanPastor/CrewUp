import { create } from 'zustand';
import { User } from '../types';
import keycloak from '../keycloak';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  initKeycloak: () => Promise<void>;
  login: () => void;
  logout: () => void;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,

  initKeycloak: async () => {
    try {
      const authenticated = await keycloak.init({
        onLoad: 'login-required', // Auto-redirect to Keycloak if not authenticated
        checkLoginIframe: false,
        pkceMethod: 'S256',
      });

      if (authenticated && keycloak.tokenParsed) {
        // Extract user info from token
        const mockUser: User = {
          id: keycloak.tokenParsed.sub || '',
          email: keycloak.tokenParsed.email || '',
          first_name: keycloak.tokenParsed.given_name || '',
          last_name: keycloak.tokenParsed.family_name || '',
          created_at: new Date().toISOString(),
        };

        set({
          user: mockUser,
          token: keycloak.token || null,
          isAuthenticated: true,
          isLoading: false,
        });

        // Setup token refresh
        setInterval(() => {
          keycloak.updateToken(70).catch(() => {
            console.error('Failed to refresh token');
          });
        }, 60000); // Refresh every minute
      } else {
        set({ isLoading: false });
      }
    } catch (error) {
      console.error('Keycloak initialization failed:', error);
      set({ isLoading: false });
    }
  },

  login: () => {
    keycloak.login();
  },

  logout: () => {
    keycloak.logout();
    set({ user: null, token: null, isAuthenticated: false });
  },

  setUser: (user: User) => {
    set({ user });
  },
}));
