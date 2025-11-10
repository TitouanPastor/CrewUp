import { useState, useEffect, useRef } from 'react';
import { Send, Users } from 'lucide-react';
import Button from '../components/ui/Button';

interface ChatMessage {
  id: string;
  sender_id: string;
  sender_name: string;
  content: string;
  created_at: string;
}

export default function GroupChatPage() {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender_id: 'user1',
      sender_name: 'John Doe',
      content: 'Hey everyone! Ready for tonight?',
      created_at: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      id: '2',
      sender_id: 'user2',
      sender_name: 'Jane Smith',
      content: 'Yes! What time should we meet?',
      created_at: new Date(Date.now() - 2400000).toISOString(),
    },
    {
      id: '3',
      sender_id: 'current-user',
      sender_name: 'You',
      content: 'How about 10 PM at the entrance?',
      created_at: new Date(Date.now() - 1200000).toISOString(),
    },
  ]);
  const [newMessage, setNewMessage] = useState('');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!newMessage.trim()) return;

    const message: ChatMessage = {
      id: Date.now().toString(),
      sender_id: 'current-user',
      sender_name: 'You',
      content: newMessage,
      created_at: new Date().toISOString(),
    };

    setMessages([...messages, message]);
    setNewMessage('');
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const getAvatarColor = (name: string) => {
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-yellow-500',
      'bg-indigo-500',
    ];
    const index = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[index % colors.length];
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] md:h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
            <Users className="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <h1 className="font-semibold text-gray-900">Party Crew</h1>
            <p className="text-sm text-gray-600">5 members</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-gray-50 p-4 space-y-4">
        {messages.map((message, index) => {
          const isCurrentUser = message.sender_id === 'current-user';
          const prevMessage = index > 0 ? messages[index - 1] : null;
          const showAvatar = !prevMessage || prevMessage.sender_id !== message.sender_id;

          return (
            <div
              key={message.id}
              className={`flex gap-3 ${isCurrentUser ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {/* Avatar */}
              <div className="flex-shrink-0 w-8">
                {showAvatar && (
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${getAvatarColor(
                      message.sender_name
                    )}`}
                  >
                    {message.sender_name.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>

              {/* Message Bubble */}
              <div className={`flex flex-col ${isCurrentUser ? 'items-end' : 'items-start'} max-w-[70%]`}>
                {!isCurrentUser && showAvatar && (
                  <span className="text-xs text-gray-600 mb-1 px-3">
                    {message.sender_name}
                  </span>
                )}
                <div
                  className={`px-4 py-2 rounded-2xl ${
                    isCurrentUser
                      ? 'bg-primary-400 text-white rounded-br-sm'
                      : 'bg-white text-gray-900 border border-gray-100 shadow-sm rounded-bl-sm'
                  }`}
                >
                  <p className="text-sm leading-relaxed">{message.content}</p>
                </div>
                <span className="text-xs text-gray-500 mt-1 px-3">
                  {formatTime(message.created_at)}
                </span>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 p-4 flex-shrink-0">
        <div className="flex gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type a message..."
            className="flex-1 px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <Button
            variant="primary"
            onClick={handleSend}
            disabled={!newMessage.trim()}
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
