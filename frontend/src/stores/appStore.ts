import { create } from 'zustand';
import { Event, Group, Message } from '../types';

interface AppState {
  events: Event[];
  selectedEvent: Event | null;
  groups: Group[];
  selectedGroup: Group | null;
  messages: Message[];
  isPartyMode: boolean;
  
  setEvents: (events: Event[]) => void;
  setSelectedEvent: (event: Event | null) => void;
  setGroups: (groups: Group[]) => void;
  setSelectedGroup: (group: Group | null) => void;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  togglePartyMode: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  events: [],
  selectedEvent: null,
  groups: [],
  selectedGroup: null,
  messages: [],
  isPartyMode: false,

  setEvents: (events) => set({ events }),
  setSelectedEvent: (event) => set({ selectedEvent: event }),
  setGroups: (groups) => set({ groups }),
  setSelectedGroup: (group) => set({ selectedGroup: group }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setMessages: (messages) => set({ messages }),
  togglePartyMode: () => set((state) => ({ isPartyMode: !state.isPartyMode })),
}));
