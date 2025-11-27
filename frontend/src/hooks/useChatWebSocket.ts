import { useEffect, useRef, useState } from 'react';
import { ChatWebSocket } from '@/services/groupService';

interface ChatMessage {
  id: string;
  user_id: string;
  username: string;
  content: string;
  timestamp: string;
  type: 'message' | 'system' | 'safety_alert';
  // Safety alert specific data
  alert_data?: {
    id: string;
    user_id: string;
    group_id?: string;
    alert_type: string;
    message?: string;
    latitude?: number;
    longitude?: number;
    created_at: string;
    resolved?: boolean;
    resolved_at?: string;
  };
}

interface UseChatWebSocketReturn {
  messages: ChatMessage[];
  sendMessage: (content: string) => void;
  isConnected: boolean;
  error: string | null;
  onAlertResolved?: (alertId: string, resolvedAt: string) => void;
}

export const useChatWebSocket = (
  groupId: string, 
  enabled: boolean = true,
  onAlertResolved?: (alertId: string, resolvedAt: string) => void
): UseChatWebSocketReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasConnected, setHasConnected] = useState(false);
  const wsRef = useRef<ChatWebSocket | null>(null);

  useEffect(() => {
    if (!enabled) return;

    // Create WebSocket connection
    const ws = new ChatWebSocket(groupId);
    wsRef.current = ws;

    // Handle incoming messages
    ws.onMessage((data) => {
      console.log('WebSocket message received:', data);
      
      if (data.type === 'message') {
        setMessages((prev) => {
          // Avoid duplicates by checking if message ID already exists
          if (prev.some(msg => msg.id === data.id)) {
            return prev;
          }
          return [
            ...prev,
            {
              id: data.id,
              user_id: data.user_id,
              username: data.username,
              content: data.content,
              timestamp: data.timestamp,
              type: 'message',
            },
          ];
        });
      } else if (data.type === 'safety_alert') {
        // Handle safety alerts
        setMessages((prev) => {
          // Avoid duplicates
          if (prev.some(msg => msg.alert_data?.id === data.alert_id)) {
            return prev;
          }
          return [
            ...prev,
            {
              id: data.alert_id, // Use alert_id as message id
              user_id: data.user_id,
              username: data.user_name || 'Unknown User',
              content: '', // Not used for safety alerts
              timestamp: data.created_at,
              type: 'safety_alert',
              alert_data: {
                id: data.alert_id,
                user_id: data.user_id,
                user_name: data.user_name,
                alert_type: data.alert_type,
                message: data.message,
                latitude: data.latitude,
                longitude: data.longitude,
                created_at: data.created_at,
                resolved: false,
              },
            },
          ];
        });
      } else if (data.type === 'alert_resolved') {
        // Handle alert resolution
        console.log('Alert resolved:', data.alert_id, data.resolved_at);
        
        // Call the callback if provided
        if (onAlertResolved) {
          onAlertResolved(data.alert_id, data.resolved_at);
        }
        
        // Also update wsMessages
        setMessages((prev) => {
          return prev.map((msg) => {
            if (msg.alert_data?.id === data.alert_id) {
              return {
                ...msg,
                alert_data: {
                  ...msg.alert_data,
                  resolved: true,
                  resolved_at: data.resolved_at,
                },
              };
            }
            return msg;
          });
        });
      }
    });

    // Handle connection open
    ws.onOpen(() => {
      setIsConnected(true);
      setHasConnected(true);
      setError(null);
    });

    // Handle connection close
    ws.onClose(() => {
      setIsConnected(false);
      if (hasConnected) {
        setError('Connection lost. Retrying...');
      }
    });

    // Handle errors
    ws.onError((err) => {
      console.error('WebSocket error:', err);
      if (hasConnected) {
        setError('Connection error. Retrying...');
      }
      setIsConnected(false);
    });

    // Connect
    ws.connect();

    // Cleanup on unmount
    return () => {
      ws.disconnect();
    };
  }, [groupId, enabled, onAlertResolved]);

  const sendMessage = (content: string) => {
    if (wsRef.current && content.trim()) {
      wsRef.current.sendMessage(content.trim());
    }
  };

  return {
    messages,
    sendMessage,
    isConnected,
    error,
  };
};
