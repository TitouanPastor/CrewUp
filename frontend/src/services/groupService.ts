import api from './api';
import keycloak from '../keycloak';

// Types
export interface Group {
  id: string;
  event_id: string;
  name: string;
  description: string | null;
  max_members: number;
  member_count: number;
  is_full: boolean;
  is_private: boolean;
  created_at: string;
  updated_at: string;
}

export interface GroupMember {
  user_id: string;
  keycloak_id?: string;  // Add keycloak_id for membership checking
  joined_at: string;
  is_admin: boolean;
}

export interface ChatMessage {
  id: string;
  group_id: string;
  sender_id: string;
  content: string;
  sent_at: string;
}

export interface CreateGroupData {
  event_id: string;
  name: string;
  description?: string;
  max_members?: number;
  is_private?: boolean;
}

export interface UpdateGroupData {
  name?: string;
  description?: string;
  max_members?: number;
  is_private?: boolean;
}

// Group CRUD
export const groupService = {
  // Create a new group
  async createGroup(data: CreateGroupData): Promise<Group> {
    const response = await api.post<Group>('/groups', data);
    return response.data;
  },

  // List groups for an event
  async listGroups(eventId?: string): Promise<{ groups: Group[]; total: number }> {
    const url = eventId ? `/groups?event_id=${eventId}` : '/groups';
    const response = await api.get<{ groups: Group[]; total: number }>(url);
    return response.data;
  },

  // Get group details
  async getGroup(groupId: string): Promise<Group> {
    const response = await api.get<Group>(`/groups/${groupId}`);
    return response.data;
  },

  // Update group (admin only)
  async updateGroup(groupId: string, data: UpdateGroupData): Promise<Group> {
    const response = await api.put<Group>(`/groups/${groupId}`, data);
    return response.data;
  },

  // Delete group (admin only)
  async deleteGroup(groupId: string): Promise<void> {
    await api.delete(`/groups/${groupId}`);
  },

  // Join a group
  async joinGroup(groupId: string): Promise<void> {
    await api.post(`/groups/${groupId}/join`);
  },

  // Leave a group
  async leaveGroup(groupId: string): Promise<void> {
    await api.delete(`/groups/${groupId}/leave`);
  },

  // List group members
  async getMembers(groupId: string): Promise<{ members: GroupMember[]; total: number }> {
    const response = await api.get<{ members: GroupMember[]; total: number }>(
      `/groups/${groupId}/members`
    );
    return response.data;
  },

  // Get message history
  async getMessages(
    groupId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<{ messages: ChatMessage[]; total: number; limit: number; offset: number }> {
    const response = await api.get<{
      messages: ChatMessage[];
      total: number;
      limit: number;
      offset: number;
    }>(`/groups/${groupId}/messages?limit=${limit}&offset=${offset}`);
    return response.data;
  },
};

// WebSocket Chat Manager
export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private groupId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: ((message: any) => void)[] = [];
  private closeHandlers: (() => void)[] = [];
  private errorHandlers: ((error: Event) => void)[] = [];
  private openHandlers: (() => void)[] = [];
  private shouldReconnect = true;

  constructor(groupId: string) {
    this.groupId = groupId;
  }

  // Connect to WebSocket
  connect(): void {
    const token = keycloak.token;

    if (!token) {
      console.error('No authentication token available');
      return;
    }

    // Build WebSocket URL based on current window location
    // In dev: Vite proxy handles /api/v1/ws/groups -> ws://localhost:8002
    // In prod: Uses same domain with wss://
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    
    const url = `${protocol}//${host}/api/v1/ws/groups/${this.groupId}?token=${token}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log(`Connected to group chat: ${this.groupId}`);
      this.reconnectAttempts = 0;
      this.openHandlers.forEach((handler) => handler());
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.messageHandlers.forEach((handler) => handler(data));
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.errorHandlers.forEach((handler) => handler(error));
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
      this.closeHandlers.forEach((handler) => handler());
      this.attemptReconnect();
    };
  }

  // Send a message
  sendMessage(content: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: 'message',
          content,
        })
      );
    } else {
      console.error('WebSocket is not connected');
    }
  }

  // Register message handler
  onMessage(handler: (message: any) => void): void {
    this.messageHandlers.push(handler);
  }

  // Register open handler
  onOpen(handler: () => void): void {
    this.openHandlers.push(handler);
  }

  // Register close handler
  onClose(handler: () => void): void {
    this.closeHandlers.push(handler);
  }

  // Register error handler
  onError(handler: (error: Event) => void): void {
    this.errorHandlers.push(handler);
  }

  // Disconnect
  disconnect(): void {
    this.shouldReconnect = false; // Stop auto-reconnection
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // Auto-reconnect logic
  private attemptReconnect(): void {
    if (!this.shouldReconnect) {
      console.log('Reconnection disabled, not attempting to reconnect');
      return;
    }
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
      );
      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  // Check connection status
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
