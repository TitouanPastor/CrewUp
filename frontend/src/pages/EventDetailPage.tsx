import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Calendar, MapPin, Users, ArrowLeft, Share2, UserPlus, Heart, Edit, XCircle, Save } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { groupService } from '@/services/groupService';
import { eventService } from '@/services/eventService';
import { userService } from '@/services/userService';
import CreateGroupDialog from '@/components/CreateGroupDialog';
import GroupList from '@/components/GroupList';
import { Event } from '@/types';
import 'leaflet/dist/leaflet.css';

export default function EventDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [event, setEvent] = useState<Event | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [groupsRefreshKey, setGroupsRefreshKey] = useState(0);
  const [groupsCount, setGroupsCount] = useState(0);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [editForm, setEditForm] = useState({
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

  useEffect(() => {
    if (id) {
      loadEvent();
      loadGroupsCount();
      loadCurrentUser();
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      loadGroupsCount();
    }
  }, [groupsRefreshKey]);

  // Initialize edit form when entering edit mode
  useEffect(() => {
    if (isEditMode && event) {
      const formatDateForInput = (dateString: string) => {
        const date = new Date(dateString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}`;
      };

      setEditForm({
        name: event.name,
        description: event.description || '',
        event_type: event.event_type || 'other',
        address: event.address,
        latitude: event.latitude?.toString() || '',
        longitude: event.longitude?.toString() || '',
        event_start: formatDateForInput(event.event_start),
        event_end: event.event_end ? formatDateForInput(event.event_end) : '',
        max_attendees: event.max_attendees?.toString() || '',
      });
    }
  }, [isEditMode, event]);

  const loadEvent = async () => {
    try {
      setLoading(true);
      const data = await eventService.getEvent(id!);
      setEvent(data);
    } catch (error) {
      console.error('Failed to load event:', error);
      toast({
        title: "Error",
        description: "Failed to load event details. Please try again later.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadGroupsCount = async () => {
    try {
      const data = await groupService.listGroups(id!);
      setGroupsCount(data.total);
    } catch (error) {
      console.error('Failed to load groups count:', error);
    }
  };

  const loadCurrentUser = async () => {
    try {
      const user = await userService.getMe();
      setCurrentUserId(user.id);
    } catch (error) {
      console.error('Failed to load current user:', error);
    }
  };

  const handleRSVP = async (status: 'going' | 'interested') => {
    try {
      await eventService.joinEvent(id!, status);
      toast({
        title: "Success",
        description: `You are now marked as ${status}!`,
      });
      // Reload event to get updated counts and user status
      loadEvent();
    } catch (error) {
      console.error('Failed to RSVP:', error);
      toast({
        title: "Error",
        description: "Failed to update your RSVP. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleCancelEvent = async () => {
    if (!window.confirm('Are you sure you want to cancel this event? This action cannot be undone.')) {
      return;
    }

    try {
      setIsCancelling(true);
      await eventService.updateEvent(id!, { is_cancelled: true });
      toast({
        title: "Event Cancelled",
        description: "This event has been marked as cancelled.",
      });
      // Reload event to show updated status
      await loadEvent();
      setIsEditMode(false);
    } catch (error) {
      console.error('Failed to cancel event:', error);
      toast({
        title: "Error",
        description: "Failed to cancel event. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsCancelling(false);
    }
  };

  const handleSaveChanges = async () => {
    if (!event) return;

    // Validation
    if (!editForm.name.trim()) {
      toast({
        title: 'Name required',
        description: 'Please enter an event name',
        variant: 'destructive',
      });
      return;
    }

    if (!editForm.address.trim()) {
      toast({
        title: 'Address required',
        description: 'Please enter an event address',
        variant: 'destructive',
      });
      return;
    }

    if (!editForm.event_start) {
      toast({
        title: 'Start time required',
        description: 'Please select an event start time',
        variant: 'destructive',
      });
      return;
    }

    if (!editForm.event_end) {
      toast({
        title: 'End time required',
        description: 'Please select an event end time',
        variant: 'destructive',
      });
      return;
    }

    // Validate end time is after start time
    if (new Date(editForm.event_end) <= new Date(editForm.event_start)) {
      toast({
        title: 'Invalid time range',
        description: 'End time must be after start time',
        variant: 'destructive',
      });
      return;
    }

    // Validate latitude/longitude pair
    if ((editForm.latitude && !editForm.longitude) || (!editForm.latitude && editForm.longitude)) {
      toast({
        title: 'Invalid coordinates',
        description: 'Both latitude and longitude must be provided together',
        variant: 'destructive',
      });
      return;
    }

    try {
      setIsSaving(true);
      await eventService.updateEvent(id!, {
        name: editForm.name.trim(),
        description: editForm.description.trim() || undefined,
        event_type: editForm.event_type as any,
        address: editForm.address.trim(),
        latitude: editForm.latitude ? parseFloat(editForm.latitude) : undefined,
        longitude: editForm.longitude ? parseFloat(editForm.longitude) : undefined,
        event_start: new Date(editForm.event_start).toISOString(),
        event_end: new Date(editForm.event_end).toISOString(),
        max_attendees: editForm.max_attendees ? parseInt(editForm.max_attendees) : null,
      });

      toast({
        title: "Changes Saved",
        description: "Event has been updated successfully.",
      });

      // Reload event to show updated data
      await loadEvent();
      setIsEditMode(false);
    } catch (error: any) {
      console.error('Failed to update event:', error);
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to update event. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleGroupCreated = () => {
    setGroupsRefreshKey((prev) => prev + 1);
  };

  const isCreator = currentUserId && event && currentUserId === event.creator_id;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <h2 className="text-2xl font-bold">Event not found</h2>
        <Button onClick={() => navigate('/events')}>Back to Events</Button>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: event.name,
        text: event.description,
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      toast({
        title: "Link copied!",
        description: "Event link copied to clipboard",
      });
    }
  };

  return (
    <div>
      <div className="max-w-5xl mx-auto px-4 md:px-6 py-6 space-y-6">
        {/* Back Button */}
        <Button
          variant="ghost"
          onClick={() => navigate('/events')}
          className="gap-2 -ml-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </Button>

        {/* Event Header */}
        <div className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 space-y-3">
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="capitalize text-sm">
                  {event.event_type}
                </Badge>
                {event.is_cancelled && (
                  <Badge variant="destructive" className="text-sm">
                    Cancelled
                  </Badge>
                )}
              </div>
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
                {event.name}
              </h1>
            </div>
            <div className="flex gap-2">
              {isCreator && !event.is_cancelled && (
                <Button
                  variant={isEditMode ? "default" : "outline"}
                  size="icon"
                  onClick={() => setIsEditMode(!isEditMode)}
                  className="flex-shrink-0"
                >
                  <Edit className="w-4 h-4" />
                </Button>
              )}
              <Button
                variant="outline"
                size="icon"
                onClick={handleShare}
                className="flex-shrink-0"
              >
                <Share2 className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-primary" />
              <span className="font-medium">{event.participant_count} going</span>
            </div>
            <div className="flex items-center gap-2">
              <Heart className="w-4 h-4 text-primary" />
              <span className="font-medium">{event.interested_count} interested</span>
            </div>
            <div className="flex items-center gap-2">
              <UserPlus className="w-4 h-4 text-primary" />
              <span className="font-medium">{groupsCount} groups</span>
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="md:col-span-2">
            <Tabs defaultValue="about" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="about">About</TabsTrigger>
                <TabsTrigger value="groups">Groups ({groupsCount})</TabsTrigger>
              </TabsList>

              <TabsContent value="about" className="space-y-6 mt-6">
                {/* Edit Form */}
                {isEditMode && isCreator && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Edit Event Details</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="col-span-2 space-y-2">
                          <Label htmlFor="edit-name">Event Name *</Label>
                          <Input
                            id="edit-name"
                            value={editForm.name}
                            onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                            maxLength={255}
                          />
                        </div>

                        <div className="col-span-2 space-y-2">
                          <Label htmlFor="edit-description">Description</Label>
                          <Textarea
                            id="edit-description"
                            value={editForm.description}
                            onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                            rows={3}
                          />
                        </div>

                        <div className="col-span-2 space-y-2">
                          <Label htmlFor="edit-event-type">Event Type</Label>
                          <Select
                            value={editForm.event_type}
                            onValueChange={(value) => setEditForm({ ...editForm, event_type: value })}
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
                          <Label htmlFor="edit-address">Address *</Label>
                          <Input
                            id="edit-address"
                            value={editForm.address}
                            onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="edit-latitude">Latitude (optional)</Label>
                          <Input
                            id="edit-latitude"
                            type="number"
                            step="any"
                            placeholder="e.g., 65.584819"
                            value={editForm.latitude}
                            onChange={(e) => setEditForm({ ...editForm, latitude: e.target.value })}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="edit-longitude">Longitude (optional)</Label>
                          <Input
                            id="edit-longitude"
                            type="number"
                            step="any"
                            placeholder="e.g., 22.154984"
                            value={editForm.longitude}
                            onChange={(e) => setEditForm({ ...editForm, longitude: e.target.value })}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="edit-start">Start Time *</Label>
                          <Input
                            id="edit-start"
                            type="datetime-local"
                            value={editForm.event_start}
                            onChange={(e) => setEditForm({ ...editForm, event_start: e.target.value })}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="edit-end">End Time *</Label>
                          <Input
                            id="edit-end"
                            type="datetime-local"
                            value={editForm.event_end}
                            min={editForm.event_start}
                            onChange={(e) => setEditForm({ ...editForm, event_end: e.target.value })}
                          />
                        </div>

                        <div className="col-span-2 space-y-2">
                          <Label htmlFor="edit-max-attendees">Max Attendees (optional)</Label>
                          <Input
                            id="edit-max-attendees"
                            type="number"
                            min={2}
                            placeholder="Leave empty for unlimited"
                            value={editForm.max_attendees}
                            onChange={(e) => setEditForm({ ...editForm, max_attendees: e.target.value })}
                          />
                          <p className="text-xs text-muted-foreground">
                            Leave empty for unlimited attendees
                          </p>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <Button
                          onClick={handleSaveChanges}
                          disabled={isSaving}
                          className="flex-1"
                        >
                          <Save className="w-4 h-4 mr-2" />
                          {isSaving ? "Saving..." : "Save Changes"}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => setIsEditMode(false)}
                          disabled={isSaving}
                        >
                          Cancel
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Description */}
                {!isEditMode && (
                  <Card>
                    <CardHeader>
                      <CardTitle>About this event</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-muted-foreground leading-relaxed">
                        {event.description}
                      </p>
                    </CardContent>
                  </Card>
                )}

                {/* Map */}
                {event.latitude && event.longitude && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Location</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="h-[300px] rounded-b-lg overflow-hidden">
                        <MapContainer
                          center={[Number(event.latitude), Number(event.longitude)]}
                          zoom={15}
                          className="h-full w-full"
                          style={{ zIndex: 0 }}
                        >
                          <TileLayer
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                          />
                          <Marker position={[Number(event.latitude), Number(event.longitude)]}>
                            <Popup>
                              <div className="p-2">
                                <p className="font-semibold">{event.name}</p>
                                <p className="text-sm text-muted-foreground">{event.address}</p>
                              </div>
                            </Popup>
                          </Marker>
                        </MapContainer>
                      </div>
                      <div className="p-6 pt-4">
                        <div className="flex items-start gap-3">
                          <MapPin className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="font-medium">{event.address}</p>
                            <Button
                              variant="link"
                              className="h-auto p-0 text-primary"
                              onClick={() =>
                                window.open(
                                  `https://maps.google.com/?q=${event.latitude},${event.longitude}`,
                                  '_blank'
                                )
                              }
                            >
                              Open in Google Maps →
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Location without map */}
                {(!event.latitude || !event.longitude) && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Location</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-start gap-3">
                        <MapPin className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                        <p className="font-medium">{event.address}</p>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              <TabsContent value="groups" className="space-y-4 mt-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">Event Groups</h3>
                    <p className="text-sm text-muted-foreground">
                      Join or create a group to meet people
                    </p>
                  </div>
                  <Button onClick={() => setShowCreateGroup(true)}>
                    <UserPlus className="w-4 h-4 mr-2" />
                    Create Group
                  </Button>
                </div>

                <GroupList eventId={id!} onRefresh={groupsRefreshKey} />
              </TabsContent>
            </Tabs>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Event Details */}
            <Card>
              <CardHeader>
                <CardTitle>Event Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <Calendar className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                    <div className="text-sm">
                      <p className="font-semibold mb-1">{formatDate(event.event_start)}</p>
                      <p className="text-muted-foreground">
                        {formatTime(event.event_start)}{event.event_end && ` - ${formatTime(event.event_end)}`}
                      </p>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Edit Mode - Cancel Event Button */}
                {isEditMode && isCreator && !event.is_cancelled && (
                  <>
                    <div className="space-y-2">
                      <Button
                        variant="destructive"
                        className="w-full"
                        onClick={handleCancelEvent}
                        disabled={isCancelling}
                      >
                        <XCircle className="w-4 h-4 mr-2" />
                        {isCancelling ? "Cancelling..." : "Cancel Event"}
                      </Button>
                    </div>
                    <Separator />
                  </>
                )}

                {/* RSVP Buttons */}
                {!event.is_cancelled && (
                  <div className="space-y-2">
                    <Button
                      className="w-full"
                      onClick={() => handleRSVP('going')}
                      variant={event.user_status === 'going' ? 'default' : 'outline'}
                    >
                      <Users className="w-4 h-4 mr-2" />
                      {event.user_status === 'going' ? "You're Going" : "I'm Going"}
                    </Button>
                    <Button
                      variant={event.user_status === 'interested' ? 'default' : 'outline'}
                      className="w-full"
                      onClick={() => handleRSVP('interested')}
                    >
                      <Heart className="w-4 h-4 mr-2" />
                      {event.user_status === 'interested' ? "You're Interested" : "Interested"}
                    </Button>
                  </div>
                )}

                <Separator />

                {/* Share Button */}
                <Button variant="outline" className="w-full" onClick={handleShare}>
                  <Share2 className="w-4 h-4 mr-2" />
                  Share Event
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Create Group Dialog */}
      <CreateGroupDialog
        eventId={id!}
        open={showCreateGroup}
        onOpenChange={setShowCreateGroup}
        onGroupCreated={handleGroupCreated}
      />
    </div>
  );
}
