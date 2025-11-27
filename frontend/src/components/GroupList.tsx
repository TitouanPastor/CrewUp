import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { useAuthStore } from '@/stores/authStore';
import { groupService, type Group, type GroupMember } from '@/services/groupService';
import { extractErrorMessage } from '@/utils/errorHandler';
import { Users, MessageCircle, Lock, Loader2, UserMinus } from 'lucide-react';

interface GroupListProps {
  eventId: string;
  onRefresh?: number; // Trigger refresh when this changes
}

export default function GroupList({ eventId, onRefresh }: GroupListProps) {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuthStore();
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [joiningGroup, setJoiningGroup] = useState<string | null>(null);
  const [leavingGroup, setLeavingGroup] = useState<string | null>(null);
  const [membershipMap, setMembershipMap] = useState<Record<string, boolean>>({});

  useEffect(() => {
    loadGroups();
  }, [eventId, onRefresh]);

  const loadGroups = async () => {
    try {
      setLoading(true);
      const data = await groupService.listGroups(eventId);
      setGroups(data.groups);
      
      // Load membership status for each group
      // Note: Only call getMembers for groups we might be in to avoid 403 errors
      if (user) {
        const membershipStatus: Record<string, boolean> = {};
        
        // First, try to join and check membership for each group
        for (const group of data.groups) {
          try {
            const membersData = await groupService.getMembers(group.id);
            membershipStatus[group.id] = membersData.members.some(
              (member: GroupMember) => member.keycloak_id === user.id
            );
          } catch (error: any) {
            // 403 means we're not a member, which is fine
            if (error.response?.status === 403) {
              membershipStatus[group.id] = false;
            } else {
              // Other errors - assume not a member
              membershipStatus[group.id] = false;
            }
          }
        }
        
        setMembershipMap(membershipStatus);
      }
    } catch (error) {
      console.error('Failed to load groups:', error);
      toast({
        title: 'Failed to load groups',
        description: 'Please try again later',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleJoinGroup = async (groupId: string) => {
    setJoiningGroup(groupId);
    try {
      await groupService.joinGroup(groupId);
      toast({
        title: 'Joined group!',
        description: 'You can now chat with group members',
      });
      // Update membership status
      setMembershipMap(prev => ({ ...prev, [groupId]: true }));
      // Navigate to chat
      navigate(`/groups/${groupId}/chat`);
    } catch (error: any) {
      console.error('Failed to join group:', error);
      const message = extractErrorMessage(error);
      toast({
        title: 'Failed to join group',
        description: message === 'Group is full' ? 'This group is full' : 'Please try again later',
        variant: 'destructive',
      });
    } finally {
      setJoiningGroup(null);
    }
  };

  const handleLeaveGroup = async (groupId: string) => {
    setLeavingGroup(groupId);
    try {
      await groupService.leaveGroup(groupId);
      toast({
        title: 'Left group',
        description: 'You have left the group',
      });
      // Update membership status
      setMembershipMap(prev => ({ ...prev, [groupId]: false }));
      // Reload groups to update member count
      loadGroups();
    } catch (error: any) {
      console.error('Failed to leave group:', error);
      toast({
        title: 'Failed to leave group',
        description: 'Please try again later',
        variant: 'destructive',
      });
    } finally {
      setLeavingGroup(null);
    }
  };

  const handleOpenChat = (groupId: string) => {
    navigate(`/groups/${groupId}/chat`);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-5 w-3/4 mb-2" />
              <Skeleton className="h-4 w-full" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-10 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (groups.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Users className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="font-semibold mb-2">No groups yet</h3>
          <p className="text-sm text-muted-foreground">
            Be the first to create a group for this event!
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {groups.map((group) => (
        <Card key={group.id} className="hover:shadow-md transition-shadow">
          <CardHeader>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <CardTitle className="text-lg">{group.name}</CardTitle>
                  {group.is_private && (
                    <Lock className="w-4 h-4 text-muted-foreground" />
                  )}
                </div>
                {group.description && (
                  <CardDescription className="line-clamp-2">
                    {group.description}
                  </CardDescription>
                )}
              </div>
              <Badge
                variant={group.is_full ? 'destructive' : 'secondary'}
                className="shrink-0"
              >
                {group.member_count}/{group.max_members}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              {membershipMap[group.id] ? (
                <>
                  <Button
                    variant="default"
                    className="flex-1"
                    onClick={() => handleOpenChat(group.id)}
                  >
                    <MessageCircle className="w-4 h-4 mr-2" />
                    Open Chat
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => handleLeaveGroup(group.id)}
                    disabled={leavingGroup === group.id}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    {leavingGroup === group.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <>
                        <UserMinus className="w-4 h-4 mr-2" />
                        Leave
                      </>
                    )}
                  </Button>
                </>
              ) : (
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => handleJoinGroup(group.id)}
                  disabled={group.is_full || joiningGroup === group.id}
                >
                  {joiningGroup === group.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : group.is_full ? (
                    'Full'
                  ) : (
                    'Join'
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
