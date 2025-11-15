import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { groupService } from '@/services/groupService';
import { Loader2 } from 'lucide-react';

interface CreateGroupDialogProps {
  eventId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onGroupCreated?: () => void;
}

export default function CreateGroupDialog({
  eventId,
  open,
  onOpenChange,
  onGroupCreated,
}: CreateGroupDialogProps) {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    max_members: 10,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast({
        title: 'Name required',
        description: 'Please enter a group name',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      const group = await groupService.createGroup({
        event_id: eventId,
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        max_members: formData.max_members,
      });

      toast({
        title: 'Group created!',
        description: `${formData.name} has been created. You are now a member.`,
      });

      onOpenChange(false);
      if (onGroupCreated) {
        onGroupCreated();
      }
      
      // Navigate to the chat page
      navigate(`/groups/${group.id}/chat`);
    } catch (error: any) {
      console.error('Failed to create group:', error);
      toast({
        title: 'Failed to create group',
        description: error.response?.data?.detail || 'Please try again later',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create New Group</DialogTitle>
          <DialogDescription>
            Start a group for this event and invite others to join
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Group Name *</Label>
            <Input
              id="name"
              placeholder="e.g., Friday Night Crew"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              disabled={loading}
              maxLength={100}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description (optional)</Label>
            <Textarea
              id="description"
              placeholder="Tell others about your group..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              disabled={loading}
              rows={3}
              maxLength={500}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="max_members">Max Members</Label>
            <Input
              id="max_members"
              type="number"
              min={2}
              max={50}
              value={formData.max_members}
              onChange={(e) =>
                setFormData({ ...formData, max_members: parseInt(e.target.value) || 10 })
              }
              disabled={loading}
            />
            <p className="text-xs text-muted-foreground">
              Maximum number of people who can join (2-50)
            </p>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Create Group
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
