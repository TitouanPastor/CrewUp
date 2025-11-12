import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, Users, ArrowLeft, MoreVertical, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface ChatMessage {
  id: string;
  sender_id: string;
  sender_name: string;
  content: string;
  created_at: string;
}

export default function GroupChatPage() {
  const { id } = useParams();
  const navigate = useNavigate();
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
    {
      id: '4',
      sender_id: 'user1',
      sender_name: 'John Doe',
      content: 'Sounds perfect! See you there 🎉',
      created_at: new Date(Date.now() - 600000).toISOString(),
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
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
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
    <div className="flex flex-col h-[calc(100dvh-8rem)] md:h-[calc(100dvh-4rem)]">
      {/* Header */}
      <div className="bg-background border-b border-border px-4 py-3 flex-shrink-0">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate(-1)}
              className="md:hidden -ml-2"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                <Users className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h1 className="font-semibold text-base">Party Crew</h1>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Users className="w-3 h-3" />
                  <span>5 members</span>
                  <span>·</span>
                  <Calendar className="w-3 h-3" />
                  <span>Friday Night Party</span>
                </div>
              </div>
            </div>
          </div>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreVertical className="w-5 h-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>View Event Details</DropdownMenuItem>
              <DropdownMenuItem>Group Members</DropdownMenuItem>
              <DropdownMenuItem className="text-destructive">Leave Group</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 bg-muted/30">
        <div className="max-w-5xl mx-auto p-4 space-y-4">
          {messages.map((message, index) => {
            const isCurrentUser = message.sender_id === 'current-user';
            const prevMessage = index > 0 ? messages[index - 1] : null;
            const showAvatar = !prevMessage || prevMessage.sender_id !== message.sender_id;
            const nextMessage = index < messages.length - 1 ? messages[index + 1] : null;
            const showTime = !nextMessage || nextMessage.sender_id !== message.sender_id;

            return (
              <div
                key={message.id}
                className={`flex gap-2 ${isCurrentUser ? 'flex-row-reverse' : 'flex-row'}`}
              >
                {/* Avatar */}
                <div className="flex-shrink-0 w-8">
                  {showAvatar && !isCurrentUser && (
                    <Avatar className="w-8 h-8">
                      <AvatarFallback className={`${getAvatarColor(message.sender_name)} text-white text-xs font-semibold`}>
                        {message.sender_name.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                  )}
                </div>

                {/* Message Bubble */}
                <div className={`flex flex-col ${isCurrentUser ? 'items-end' : 'items-start'} max-w-[85%] md:max-w-[70%]`}>
                  {!isCurrentUser && showAvatar && (
                    <span className="text-xs font-medium text-muted-foreground mb-1 px-3">
                      {message.sender_name}
                    </span>
                  )}
                  <div
                    className={`px-4 py-2.5 rounded-2xl ${
                      isCurrentUser
                        ? 'bg-primary text-primary-foreground rounded-br-md'
                        : 'bg-background border border-border rounded-bl-md'
                    }`}
                  >
                    <p className="text-sm leading-relaxed break-words">{message.content}</p>
                  </div>
                  {showTime && (
                    <span className="text-xs text-muted-foreground mt-1 px-3">
                      {formatTime(message.created_at)}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="bg-background border-t border-border p-4 flex-shrink-0 safe-area-bottom">
        <div className="max-w-5xl mx-auto flex gap-2">
          <Input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder="Type a message..."
            className="flex-1"
          />
          <Button
            onClick={handleSend}
            disabled={!newMessage.trim()}
            size="icon"
            className="flex-shrink-0"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Safe area for iOS */}
      <style>{`
        .safe-area-bottom {
          padding-bottom: max(1rem, env(safe-area-inset-bottom));
        }
      `}</style>
    </div>
  );
}
