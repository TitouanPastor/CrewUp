import { useEffect, useRef, useState } from 'react';
import { ChatWebSocket } from '@/services/groupService';

interface ChatMessage {
  id: string;
  user_id: string;
  username: string;
  content: string;
  timestamp: string;
  type: 'message' | 'system';
}

interface UseChatWebSocketReturn {
  messages: ChatMessage[];
  sendMessage: (content: string) => void;
  isConnected: boolean;
  error: string | null;
}

export const useChatWebSocket = (groupId: string, enabled: boolean = true): UseChatWebSocketReturn => {
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
  }, [groupId, enabled]);

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
