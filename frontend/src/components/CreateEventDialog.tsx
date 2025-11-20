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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AddressAutocomplete } from '@/components/ui/address-autocomplete';
import { useToast } from '@/hooks/use-toast';
import { eventService } from '@/services/eventService';
import { Loader2 } from 'lucide-react';

interface CreateEventDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onEventCreated?: () => void;
}

export default function CreateEventDialog({
  open,
  onOpenChange,
  onEventCreated,
}: CreateEventDialogProps) {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);

  // Calculate minimum start time (30 minutes from now)
  const getMinStartTime = () => {
    const date = new Date();
    date.setMinutes(date.getMinutes() + 30);
    return date.toISOString().slice(0, 16);
  };

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    event_type: 'other',
    address: '',
    latitude: '',
    longitude: '',
    event_start: '',
    event_end: '',
    max_attendees: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast({
        title: 'Name required',
        description: 'Please enter an event name',
        variant: 'destructive',
      });
      return;
    }

    if (!formData.address.trim()) {
      toast({
        title: 'Address required',
        description: 'Please enter an event address',
        variant: 'destructive',
      });
      return;
    }

    if (!formData.event_start) {
      toast({
        title: 'Start time required',
        description: 'Please select an event start time',
        variant: 'destructive',
      });
      return;
    }

    if (!formData.event_end) {
      toast({
        title: 'End time required',
        description: 'Please select an event end time',
        variant: 'destructive',
      });
      return;
    }

    // Validate end time is after start time
    if (new Date(formData.event_end) <= new Date(formData.event_start)) {
      toast({
        title: 'Invalid time range',
        description: 'End time must be after start time',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      const event = await eventService.createEvent({
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        event_type: formData.event_type as any,
        address: formData.address.trim(),
        latitude: formData.latitude ? parseFloat(formData.latitude) : undefined,
        longitude: formData.longitude ? parseFloat(formData.longitude) : undefined,
        event_start: new Date(formData.event_start).toISOString(),
        event_end: new Date(formData.event_end).toISOString(),
        max_attendees: formData.max_attendees ? parseInt(formData.max_attendees) : null,
      });

      toast({
        title: 'Event created!',
        description: `${formData.name} has been created successfully.`,
      });

      onOpenChange(false);
      if (onEventCreated) {
        onEventCreated();
      }

      // Navigate to the event detail page
      navigate(`/events/${event.id}`);
    } catch (error: any) {
      console.error('Failed to create event:', error);
      toast({
        title: 'Failed to create event',
        description: error.response?.data?.detail || 'Please try again later',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Event</DialogTitle>
          <DialogDescription>
            Create an event and invite others to join
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2 space-y-2">
              <Label htmlFor="name">Event Name *</Label>
              <Input
                id="name"
                placeholder="e.g., Friday Night Party"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                disabled={loading}
                maxLength={255}
              />
            </div>

            <div className="col-span-2 space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Tell others about your event..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                disabled={loading}
                rows={3}
              />
            </div>

            <div className="col-span-2 space-y-2">
              <Label htmlFor="event_type">Event Type</Label>
              <Select
                value={formData.event_type}
                onValueChange={(value) => setFormData({ ...formData, event_type: value })}
                disabled={loading}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bar">Bar</SelectItem>
                  <SelectItem value="club">Club</SelectItem>
                  <SelectItem value="concert">Concert</SelectItem>
                  <SelectItem value="party">Party</SelectItem>
                  <SelectItem value="restaurant">Restaurant</SelectItem>
                  <SelectItem value="outdoor">Outdoor</SelectItem>
                  <SelectItem value="sports">Sports</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="col-span-2 space-y-2">
              <Label htmlFor="address">Address *</Label>
              <AddressAutocomplete
                id="address"
                placeholder="Search for an address..."
                value={formData.address}
                onChange={(value) => setFormData({ ...formData, address: value })}
                onSelect={(address, lat, lon) => {
                  setFormData({
                    ...formData,
                    address: address,
                    latitude: lat.toString(),
                    longitude: lon.toString(),
                  });
                }}
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground">
                Start typing to search for an address. Selecting a suggestion will auto-fill coordinates.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="latitude">Latitude (optional)</Label>
              <Input
                id="latitude"
                type="number"
                step="any"
                placeholder="e.g., 65.584819"
                value={formData.latitude}
                onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="longitude">Longitude (optional)</Label>
              <Input
                id="longitude"
                type="number"
                step="any"
                placeholder="e.g., 22.154984"
                value={formData.longitude}
                onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="event_start">Start Time *</Label>
              <Input
                id="event_start"
                type="datetime-local"
                value={formData.event_start}
                min={getMinStartTime()}
                onChange={(e) => setFormData({ ...formData, event_start: e.target.value })}
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="event_end">End Time *</Label>
              <Input
                id="event_end"
                type="datetime-local"
                value={formData.event_end}
                min={formData.event_start}
                onChange={(e) => setFormData({ ...formData, event_end: e.target.value })}
                disabled={loading}
              />
            </div>

            <div className="col-span-2 space-y-2">
              <Label htmlFor="max_attendees">Max Attendees (optional)</Label>
              <Input
                id="max_attendees"
                type="number"
                min={2}
                placeholder="Leave empty for unlimited"
                value={formData.max_attendees}
                onChange={(e) => setFormData({ ...formData, max_attendees: e.target.value })}
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground">
                Maximum number of attendees (minimum 2 if set, leave empty for unlimited)
              </p>
            </div>
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
              Create Event
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
