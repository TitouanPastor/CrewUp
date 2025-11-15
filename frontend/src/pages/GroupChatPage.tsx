import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, Users, ArrowLeft, MoreVertical, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/hooks/use-toast';
import { useChatWebSocket } from '@/hooks/useChatWebSocket';
import { groupService, type Group } from '@/services/groupService';
import keycloak from '@/keycloak';

interface Message {
  id: string;
  user_id: string;
  username: string;
  content: string;
  timestamp: string;
  type: 'message' | 'system';
}

export default function GroupChatPage() {
  const { id: groupId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const [group, setGroup] = useState<Group | null>(null);
  const [loadingGroup, setLoadingGroup] = useState(true);
  const [isMember, setIsMember] = useState(false);
  const [historyMessages, setHistoryMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');

  const { messages: wsMessages, sendMessage, isConnected, error } = useChatWebSocket(
    groupId!,
    isMember // Only connect if user is a member
  );

  // Combined messages (history + real-time)
  const allMessages = [...historyMessages, ...wsMessages];

  const currentUserId = keycloak.tokenParsed?.sub || '';

  useEffect(() => {
    if (!groupId) return;

    const loadGroupData = async () => {
      try {
        // Load group details
        const groupData = await groupService.getGroup(groupId);
        setGroup(groupData);

        // Check membership
        try {
          const { members } = await groupService.getMembers(groupId);
          const isUserMember = members.some((m) => m.keycloak_id === currentUserId);
          setIsMember(isUserMember);

          if (!isUserMember) {
            toast({
              title: 'Access denied',
              description: 'You must be a member of this group to view the chat',
              variant: 'destructive',
            });
            navigate(-1);
            return;
          }

          // Load message history only if member
          const { messages } = await groupService.getMessages(groupId, 100);
          setHistoryMessages(
            messages.map((msg) => ({
              id: msg.id,
              user_id: msg.sender_id,
              username: msg.sender_id.slice(0, 8), // Use user ID as fallback username
              content: msg.content,
              timestamp: msg.sent_at,
              type: 'message' as const,
            }))
          );
        } catch (memberError: any) {
          // 403 means not a member
          if (memberError.response?.status === 403) {
            toast({
              title: 'Access denied',
              description: 'You must be a member of this group to view the chat',
              variant: 'destructive',
            });
            navigate(-1);
          }
          return;
        }
      } catch (error: any) {
        console.error('Failed to load group:', error);
        toast({
          title: 'Failed to load group',
          description: error.response?.data?.detail || 'Please try again',
          variant: 'destructive',
        });
        navigate(-1);
      } finally {
        setLoadingGroup(false);
      }
    };

    loadGroupData();
  }, [groupId]);

  useEffect(() => {
    scrollToBottom();
  }, [allMessages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = () => {
    if (!newMessage.trim()) return;
    sendMessage(newMessage.trim());
    setNewMessage('');
  };

  const handleLeaveGroup = async () => {
    if (!groupId) return;
    
    try {
      await groupService.leaveGroup(groupId);
      toast({
        title: 'Left group',
        description: 'You have left this group',
      });
      navigate(-1);
    } catch (error) {
      toast({
        title: 'Failed to leave group',
        description: 'Please try again',
        variant: 'destructive',
      });
    }
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

  const getAvatarColor = (userId: string) => {
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-yellow-500',
      'bg-indigo-500',
    ];
    const index = userId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[index % colors.length];
  };

  if (loadingGroup) {
    return (
      <div className="flex items-center justify-center h-[calc(100dvh-8rem)] md:h-[calc(100dvh-4rem)]">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!group) {
    return (
      <div className="flex items-center justify-center h-[calc(100dvh-5rem)] md:h-[calc(100dvh-4rem)]">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="font-semibold mb-2">Group not found</h3>
          <Button onClick={() => navigate(-1)}>Go Back</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100dvh-5rem)] md:h-[calc(100dvh-4rem)]">
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
                <h1 className="font-semibold text-base">{group.name}</h1>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Users className="w-3 h-3" />
                  <span>{group.member_count} members</span>
                  {!isConnected && (
                    <>
                      <span>·</span>
                      <Badge variant="outline" className="h-5 px-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-yellow-500 mr-1.5" />
                        Connecting...
                      </Badge>
                    </>
                  )}
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
              <DropdownMenuItem onClick={() => navigate(-1)}>
                Back to Event
              </DropdownMenuItem>
              <DropdownMenuItem className="text-destructive" onClick={handleLeaveGroup}>
                Leave Group
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Connection Error */}
      {error && (
        <Alert variant="destructive" className="m-4 max-w-5xl mx-auto">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1 bg-muted/30">
        <div className="max-w-5xl mx-auto p-4 space-y-4">
          {allMessages.length === 0 && (
            <div className="text-center py-12">
              <Users className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="font-semibold mb-2">No messages yet</h3>
              <p className="text-sm text-muted-foreground">
                Be the first to say something!
              </p>
            </div>
          )}

          {allMessages.map((message, index) => {
            const isCurrentUser = message.user_id === currentUserId;
            const prevMessage = index > 0 ? allMessages[index - 1] : null;
            const showAvatar = !prevMessage || prevMessage.user_id !== message.user_id;
            const nextMessage = index < allMessages.length - 1 ? allMessages[index + 1] : null;
            const showTime = !nextMessage || nextMessage.user_id !== message.user_id;

            return (
              <div
                key={message.id}
                className={`flex gap-2 ${isCurrentUser ? 'flex-row-reverse' : 'flex-row'}`}
              >
                {/* Avatar */}
                <div className="flex-shrink-0 w-8">
                  {showAvatar && !isCurrentUser && (
                    <Avatar className="w-8 h-8">
                      <AvatarFallback className={`${getAvatarColor(message.user_id)} text-white text-xs font-semibold`}>
                        {message.username.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                  )}
                </div>

                {/* Message Bubble */}
                <div className={`flex flex-col ${isCurrentUser ? 'items-end' : 'items-start'} max-w-[85%] md:max-w-[70%]`}>
                  {!isCurrentUser && showAvatar && (
                    <span className="text-xs font-medium text-muted-foreground mb-1 px-3">
                      {message.username}
                    </span>
                  )}
                  <div
                    className={`px-4 py-2.5 rounded-2xl ${
                      isCurrentUser
                        ? 'bg-primary text-primary-foreground rounded-br-md'
                        : 'bg-background border border-border rounded-bl-md'
                    }`}
                  >
                    <p className="text-sm leading-relaxed break-words whitespace-pre-wrap">{message.content}</p>
                  </div>
                  {showTime && (
                    <span className="text-xs text-muted-foreground mt-1 px-3">
                      {formatTime(message.timestamp)}
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
      <div className="bg-background border-t border-border p-4 flex-shrink-0">
        <div className="max-w-5xl mx-auto flex gap-2">
          <Input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder={isConnected ? "Type a message..." : "Connecting..."}
            className="flex-1"
            disabled={!isConnected}
          />
          <Button
            onClick={handleSend}
            disabled={!newMessage.trim() || !isConnected}
            size="icon"
            className="flex-shrink-0"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
