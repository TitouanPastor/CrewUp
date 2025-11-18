import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Calendar, MapPin, Users, ArrowLeft, Share2, UserPlus, Heart } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { groupService } from '@/services/groupService';
import { eventService } from '@/services/eventService';
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

  useEffect(() => {
    if (id) {
      loadEvent();
      loadGroupsCount();
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      loadGroupsCount();
    }
  }, [groupsRefreshKey]);

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

  const handleGroupCreated = () => {
    setGroupsRefreshKey((prev) => prev + 1);
  };

  return (
    <div>
      <div className="max-w-5xl mx-auto px-4 md:px-6 py-6 space-y-6">
        {/* Back Button */}
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="gap-2 -ml-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </Button>

        {/* Event Header */}
        <div className="space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 space-y-3">
              <Badge variant="secondary" className="capitalize text-sm">
                {event.event_type}
              </Badge>
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
                {event.name}
              </h1>
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={handleShare}
              className="flex-shrink-0"
            >
              <Share2 className="w-4 h-4" />
            </Button>
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
                {/* Description */}
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

                {/* RSVP Buttons */}
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

                <Separator />

                {/* Share Button */}
                <Button variant="outline" className="w-full" onClick={handleShare}>
                  <Share2 className="w-4 h-4 mr-2" />
                  Share Event
                </Button>
              </CardContent>
            </Card>

            {/* Attendees Preview */}
            <Card>
              <CardHeader>
                <CardTitle>Who's Going</CardTitle>
              </CardHeader>
              <CardContent>
                {event.participant_count > 0 ? (
                  <>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="flex -space-x-2">
                        {[...Array(Math.min(4, event.participant_count))].map((_, i) => (
                          <div
                            key={i}
                            className="w-8 h-8 rounded-full bg-primary/10 border-2 border-background flex items-center justify-center text-xs font-medium"
                          >
                            {String.fromCharCode(65 + i)}
                          </div>
                        ))}
                      </div>
                      {event.participant_count > 4 && (
                        <span className="text-sm text-muted-foreground">
                          +{event.participant_count - 4} others
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Join them and make new friends!
                    </p>
                  </>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Be the first to say you're going!
                  </p>
                )}
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
