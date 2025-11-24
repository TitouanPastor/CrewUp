import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Calendar, MapPin, Users, ArrowLeft, Share2, UserPlus, Heart, Edit, XCircle, Save } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AddressAutocomplete } from '@/components/ui/address-autocomplete';
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

  // ✅ new loading strategy
  const [event, setEvent] = useState<Event | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [reloading, setReloading] = useState(false);

  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [groupsRefreshKey, setGroupsRefreshKey] = useState(0);
  const [groupsCount, setGroupsCount] = useState(0);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('about');

  const [editForm, setEditForm] = useState<{
    name: string;
    description: string;
    event_type: 'bar' | 'club' | 'concert' | 'party' | 'restaurant' | 'outdoor' | 'sports' | 'other';
    address: string;
    latitude: string;
    longitude: string;
    event_start: string;
    event_end: string;
    max_attendees: string;
  }>({
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

  // ✅ initial load only — prevents flicker
  useEffect(() => {
    if (!id) return;

    const loadInitial = async () => {
      try {
        setInitialLoading(true);

        const [eventData, groupsData, user] = await Promise.all([
          eventService.getEvent(id),
          groupService.listGroups(id),
          userService.getMe(),
        ]);

        setEvent(eventData);
        setGroupsCount(groupsData.total);
        setCurrentUserId(user.id);
      } catch (error) {
        console.error('Failed to load event:', error);
        toast({
          title: "Error",
          description: "Failed to load event details. Please try again later.",
          variant: "destructive",
        });
      } finally {
        setInitialLoading(false);
      }
    };

    loadInitial();
  }, [id]);

  // ✅ background soft refresh — no flicker
  const reloadEvent = async () => {
    if (!id) return;
    try {
      setReloading(true);
      const data = await eventService.getEvent(id);
      setEvent(data);
    } catch (err) {
      console.error('Failed to refresh event:', err);
    } finally {
      setReloading(false);
    }
  };

  // ✅ refresh groups only when needed
  useEffect(() => {
    if (!id) return;

    const fetchGroups = async () => {
      try {
        const data = await groupService.listGroups(id);
        setGroupsCount(data.total);
      } catch (err) {
        console.error('Failed to load groups count:', err);
      }
    };

    fetchGroups();
  }, [groupsRefreshKey, id]);

  // ✅ hydrate edit form when switching modes
  useEffect(() => {
    if (!isEditMode || !event) return;

    const formatDateForInput = (dateString: string) => {
      const date = new Date(dateString);
      return date.toISOString().slice(0, 16);
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
  }, [isEditMode, event]);

  // ✅ RSVP — already optimistically correct, just swap loadEvent → reloadEvent
  const handleRSVP = async (status: 'going' | 'interested') => {
    if (!event) return;

    const previous = structuredClone(event);

    let going = event.participant_count || 0;
    let interested = event.interested_count || 0;

    if (event.user_status === 'going') going--;
    if (event.user_status === 'interested') interested--;

    if (status === 'going') going++;
    if (status === 'interested') interested++;

    setEvent({ ...event, user_status: status, participant_count: going, interested_count: interested });

    try {
      await eventService.joinEvent(id!, status);
      reloadEvent(); // ✅ smooth refresh
    } catch {
      setEvent(previous);
      toast({ title: "Error", description: "Failed to update RSVP.", variant: "destructive" });
    }
  };

  const handleLeaveEvent = async () => {
    if (!event) return;

    const previous = structuredClone(event);

    let going = event.participant_count || 0;
    let interested = event.interested_count || 0;

    if (event.user_status === 'going') going--;
    if (event.user_status === 'interested') interested--;

    setEvent({ ...event, user_status: null, participant_count: going, interested_count: interested });

    try {
      await eventService.leaveEvent(id!);
      reloadEvent();
    } catch {
      setEvent(previous);
      toast({ title: "Error", description: "Failed to update RSVP.", variant: "destructive" });
    }
  };

  // ✅ editing — remove flicker, keep smooth UI
  const handleSaveChanges = async () => {
    if (!event) return;

    try {
      setIsSaving(true);

      await eventService.updateEvent(id!, {
        name: editForm.name.trim(),
        description: editForm.description.trim() || undefined,
        event_type: editForm.event_type,
        address: editForm.address.trim(),
        latitude: editForm.latitude ? Number(editForm.latitude) : undefined,
        longitude: editForm.longitude ? Number(editForm.longitude) : undefined,
        event_start: new Date(editForm.event_start).toISOString(),
        event_end: editForm.event_end ? new Date(editForm.event_end).toISOString() : undefined,
        max_attendees: editForm.max_attendees ? Number(editForm.max_attendees) : null,
      });

      toast({ title: "Changes Saved", description: "Event updated successfully." });

      reloadEvent(); // ✅ instead of loadEvent()
      setIsEditMode(false);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to update event.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancelEvent = async () => {
    if (!confirm("Are you sure?")) return;

    try {
      setIsCancelling(true);
      await eventService.updateEvent(id!, { is_cancelled: true });
      reloadEvent();
      setIsEditMode(false);
    } finally {
      setIsCancelling(false);
    }
  };

  const handleUncancelEvent = async () => {
    if (!confirm("Restore event?")) return;

    try {
      setIsCancelling(true);
      await eventService.updateEvent(id!, { is_cancelled: false });
      reloadEvent();
      setIsEditMode(false);
    } finally {
      setIsCancelling(false);
    }
  };

  const handleGroupCreated = () => setGroupsRefreshKey(k => k + 1);

  const isCreator = currentUserId && event && currentUserId === event.creator_id;

  // ✅ only show full-screen spinner on first load
  if (initialLoading) {
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

  const formatDate = (dateString: string) =>
    new Date(dateString).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

  const formatTime = (dateString: string) =>
    new Date(dateString).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({ title: event.name, text: event.description, url: window.location.href });
    } else {
      navigator.clipboard.writeText(window.location.href);
      toast({ title: "Link copied!", description: "Event link copied to clipboard" });
    }
  };

  return (
    <div>
      {/* Background refresh indicator */}
      {reloading && (
        <div className="fixed top-0 md:top-16 left-0 right-0 h-[2px] bg-primary animate-pulse z-[9999]" />
      )}
      {/* Sticky Header with Event Info + Tabs */}
      <div className="relative">
        <div className="fixed top-0 md:top-16 inset-x-0 z-40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
          <div className="max-w-5xl mx-auto px-4 md:px-6">
            {/* Top row: Back, Title, Type, Actions */}
            <div className="flex items-center justify-between gap-3 pt-3">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/events')}
                  className="flex-shrink-0 h-8 w-8 p-0"
                >
                  <ArrowLeft className="w-4 h-4" />
                </Button>
                <h1 className="font-semibold truncate text-sm md:text-base">{event.name}</h1>
                <Badge variant="secondary" className="capitalize text-xs flex-shrink-0">
                  {event.event_type}
                </Badge>
              </div>

              <div className="flex items-center gap-1 flex-shrink-0">
                {isCreator && (
                  <Button
                    variant={isEditMode ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setIsEditMode(!isEditMode)}
                    className="h-8 w-8 p-0"
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleShare}
                  className="h-8 w-8 p-0"
                >
                  <Share2 className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Bottom row: Tabs */}
            <div className="flex gap-6 -mb-px">
              <button
                onClick={() => setActiveTab('about')}
                className={`py-3 px-1 text-sm font-medium border-b-2 transition-colors ${activeTab === 'about'
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
              >
                About
              </button>
              <button
                onClick={() => setActiveTab('groups')}
                className={`py-3 px-1 text-sm font-medium border-b-2 transition-colors ${activeTab === 'groups'
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
              >
                Groups ({groupsCount})
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 md:px-6 pt-28 md:pt-28 pb-6 space-y-6">
        {/* Event Header - Full version for initial context */}
        <div className="space-y-4">
          {event.is_cancelled && (
            <Badge variant="destructive" className="text-sm">
              Cancelled
            </Badge>
          )}

          {/* Quick Stats */}
          <div className="flex items-center gap-6 text-sm text-muted-foreground flex-wrap">
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
            {/* About Tab */}
            {activeTab === 'about' && (
              <div className="space-y-6">
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
                            onValueChange={(value) => setEditForm({ ...editForm, event_type: value as typeof editForm.event_type })}
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
                          <AddressAutocomplete
                            id="edit-address"
                            placeholder="Search for an address..."
                            value={editForm.address}
                            onChange={(value) => setEditForm({ ...editForm, address: value })}
                            onSelect={(address, lat, lon) => {
                              setEditForm({
                                ...editForm,
                                address: address,
                                latitude: lat.toString(),
                                longitude: lon.toString(),
                              });
                            }}
                          />
                          <p className="text-xs text-muted-foreground">
                            Start typing to search for an address. Selecting a suggestion will auto-fill coordinates.
                          </p>
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
              </div>
            )}

            {/* Groups Tab */}
            {activeTab === 'groups' && (
              <div className="space-y-4">
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
              </div>
            )}
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

                {/* Edit Mode - Cancel/Un-cancel Event Button */}
                {isEditMode && isCreator && (
                  <>
                    <div className="space-y-2">
                      {event.is_cancelled ? (
                        <Button
                          variant="default"
                          className="w-full"
                          onClick={handleUncancelEvent}
                          disabled={isCancelling}
                        >
                          <XCircle className="w-4 h-4 mr-2" />
                          {isCancelling ? "Restoring..." : "Un-cancel Event"}
                        </Button>
                      ) : (
                        <Button
                          variant="destructive"
                          className="w-full"
                          onClick={handleCancelEvent}
                          disabled={isCancelling}
                        >
                          <XCircle className="w-4 h-4 mr-2" />
                          {isCancelling ? "Cancelling..." : "Cancel Event"}
                        </Button>
                      )}
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
                    <Button
                      variant={event.user_status === 'not_going' ? 'default' : 'outline'}
                      className="w-full"
                      onClick={handleLeaveEvent}
                    >
                      <XCircle className="w-4 h-4 mr-2" />
                      {event.user_status === 'not_going' ? "You're Not Going" : "Not Going"}
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
