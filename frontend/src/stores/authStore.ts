import { create } from 'zustand';
import { User } from '../types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
}

interface RegisterData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  bio?: string;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),

  login: async (email: string, _password: string) => {
    // TODO: Call API
    // For now, mock login
    const mockUser: User = {
      id: 1,
      email,
      first_name: 'John',
      last_name: 'Doe',
      bio: 'Party enthusiast!',
      created_at: new Date().toISOString(),
      reputation: {
        average_rating: 4.5,
        total_reviews: 12,
      },
    };
    const mockToken = 'mock-jwt-token';
    
    localStorage.setItem('token', mockToken);
    set({ user: mockUser, token: mockToken, isAuthenticated: true });
  },

  register: async (data: RegisterData) => {
    // TODO: Call API
    const mockUser: User = {
      id: 2,
      email: data.email,
      first_name: data.first_name,
      last_name: data.last_name,
      bio: data.bio,
      created_at: new Date().toISOString(),
    };
    const mockToken = 'mock-jwt-token';
    
    localStorage.setItem('token', mockToken);
    set({ user: mockUser, token: mockToken, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, token: null, isAuthenticated: false });
  },

  setUser: (user: User) => {
    set({ user });
  },
}));
