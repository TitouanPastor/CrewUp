import { create } from 'zustand';
import { User } from '../types';
import keycloak from '../keycloak';
import { userService } from '../services/userService';

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

// Flag to prevent double initialization
let isInitializing = false;
let isInitialized = false;

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,

  initKeycloak: async () => {
    // Prevent multiple initializations
    if (isInitializing || isInitialized) {
      return;
    }
    
    isInitializing = true;
    
    try {
      const authenticated = await keycloak.init({
        onLoad: 'login-required', // Auto-redirect to Keycloak if not authenticated
        checkLoginIframe: false,
        pkceMethod: 'S256',
      });
      
      isInitialized = true;

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

        // Create/sync user profile in database
        try {
          await userService.createProfile();
          console.log('User profile synced with database');
        } catch (error) {
          console.error('Failed to sync user profile:', error);
          // Non-blocking: user can still use the app even if profile sync fails
        }

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
    } finally {
      isInitializing = false;
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
