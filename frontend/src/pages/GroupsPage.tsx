import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageCircle, Users, Clock, Search, Calendar } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { groupService, type Group, type ChatMessage } from '@/services/groupService';
import { eventService } from '@/services/eventService';
import { extractErrorMessage } from '@/utils/errorHandler';
import { formatDistanceToNow } from 'date-fns';
import keycloak from '@/keycloak';
import type { Event } from '@/types';

interface GroupWithDetails extends Group {
  lastMessage?: ChatMessage;
  event?: Event;
}

export default function GroupsPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [groups, setGroups] = useState<GroupWithDetails[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadMyGroups();
  }, []);

  const loadMyGroups = async () => {
    try {
      setLoading(true);

      // 1. Get all groups (without event filter to get user's groups)
      const { groups: allGroups } = await groupService.listGroups();

      // 2. For each group, check membership and fetch details only if user is a member
      const groupsWithDetailsPromises = allGroups.map(async (group): Promise<GroupWithDetails | null> => {
        try {
          // Check if user is a member of this group
          const { members } = await groupService.getMembers(group.id);
          const keycloakId = keycloak.tokenParsed?.sub;
          const isMember = members.some((m) => m.keycloak_id === keycloakId);

          // Skip this group if user is not a member
          if (!isMember) {
            return null;
          }

          // Fetch last message
          const { messages } = await groupService.getMessages(group.id, 1, 0);
          const lastMessage = messages[0];

          // Fetch event details
          let event: Event | undefined;
          try {
            event = await eventService.getEvent(group.event_id);
          } catch {
            // Event might be deleted or inaccessible
            event = undefined;
          }

          return {
            ...group,
            lastMessage,
            event,
          };
        } catch (error) {
          // If we can't fetch details (e.g., 403 not a member), skip this group
          console.error(`Failed to load details for group ${group.id}:`, error);
          return null;
        }
      });

      const groupsWithDetails = await Promise.all(groupsWithDetailsPromises);

      // Filter out null entries (groups where user is not a member)
      const validGroups = groupsWithDetails.filter((g): g is GroupWithDetails => g !== null);

      // Sort by last message time (most recent first)
      validGroups.sort((a, b) => {
        const aMsg = a.lastMessage;
        const bMsg = b.lastMessage;
        if (!aMsg && !bMsg) return 0;
        if (!aMsg) return 1;
        if (!bMsg) return -1;
        return new Date(bMsg.sent_at).getTime() - new Date(aMsg.sent_at).getTime();
      });

      setGroups(validGroups);
    } catch (error) {
      console.error('Failed to load groups:', error);
      toast({
        title: 'Error',
        description: extractErrorMessage(error),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const filteredGroups = groups.filter((group) =>
    group.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    group.event?.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatLastMessageTime = (sentAt: string) => {
    try {
      return formatDistanceToNow(new Date(sentAt), { addSuffix: true });
    } catch {
      return '';
    }
  };

  const truncateMessage = (content: string, maxLength: number = 60) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  const getMessagePreview = (message: ChatMessage) => {
    // Try to parse as JSON (for system messages like alerts)
    try {
      const parsed = JSON.parse(message.content);
      if (parsed.type === 'safety_alert') {
        return `🚨 ${parsed.user_name} sent a safety alert`;
      }
      if (parsed.type === 'alert_resolved') {
        return `✅ Alert resolved by ${parsed.resolver_name}`;
      }
    } catch {
      // Regular text message
    }
    return truncateMessage(message.content);
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-6">
          <Skeleton className="h-10 w-48 mb-4" />
          <Skeleton className="h-12 w-full" />
        </div>
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-4 flex items-center gap-2">
          <MessageCircle className="w-8 h-8" />
          My Groups
        </h1>
        
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
          <Input
            type="text"
            placeholder="Search groups or events..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Groups List */}
      {filteredGroups.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <MessageCircle className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-xl font-semibold mb-2">
              {searchQuery ? 'No groups found' : 'No groups yet'}
            </h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery
                ? 'Try a different search term'
                : 'Join an event and create or join a group to start chatting'}
            </p>
            {!searchQuery && (
              <button
                onClick={() => navigate('/events')}
                className="text-primary hover:underline"
              >
                Browse Events →
              </button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredGroups.map((group) => (
            <Card
              key={group.id}
              className="hover:shadow-md transition-all cursor-pointer border-l-4 border-l-primary/20 hover:border-l-primary"
              onClick={() => navigate(`/groups/${group.id}/chat`)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  {/* Left: Group info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-lg truncate">
                        {group.name}
                      </h3>
                      {group.is_private && (
                        <Badge variant="secondary" className="text-xs">
                          Private
                        </Badge>
                      )}
                    </div>

                    {/* Event name */}
                    {group.event && (
                      <div className="flex items-center gap-1 text-sm text-muted-foreground mb-2">
                        <Calendar className="w-4 h-4" />
                        <span className="truncate">{group.event.name}</span>
                      </div>
                    )}

                    {/* Last message */}
                    {group.lastMessage ? (
                      <div className="flex items-start gap-2 text-sm">
                        <MessageCircle className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-muted-foreground truncate">
                            {group.lastMessage.sender_first_name && (
                              <span className="font-medium">
                                {group.lastMessage.sender_first_name}:{' '}
                              </span>
                            )}
                            {getMessagePreview(group.lastMessage)}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground italic">
                        No messages yet
                      </p>
                    )}
                  </div>

                  {/* Right: Members & time */}
                  <div className="flex flex-col items-end gap-2 flex-shrink-0">
                    <div className="flex items-center gap-1 text-sm text-muted-foreground">
                      <Users className="w-4 h-4" />
                      <span>{group.member_count}</span>
                    </div>
                    {group.lastMessage && (
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="w-3 h-3" />
                        <span>{formatLastMessageTime(group.lastMessage.sent_at)}</span>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Summary */}
      {filteredGroups.length > 0 && (
        <div className="mt-6 text-center text-sm text-muted-foreground">
          {filteredGroups.length === groups.length ? (
            <p>{groups.length} group{groups.length !== 1 ? 's' : ''}</p>
          ) : (
            <p>
              Showing {filteredGroups.length} of {groups.length} group{groups.length !== 1 ? 's' : ''}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
