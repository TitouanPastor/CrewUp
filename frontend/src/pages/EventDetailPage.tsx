import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Calendar, MapPin, Users, ArrowLeft, Share2, UserPlus } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import 'leaflet/dist/leaflet.css';

export default function EventDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [showJoinModal, setShowJoinModal] = useState(false);

  // Mock event data
  const event = {
    id: Number(id),
    name: 'Friday Night at Bishops Arms',
    description: 'Join us for an amazing Friday night! Great music, drinks, and vibes. Perfect opportunity to meet new people and have fun. DJ starts at 10 PM. We have special student discounts and a great atmosphere. Don\'t miss out on the best party of the week!',
    event_type: 'bar',
    address: 'Storgatan 15, Luleå',
    latitude: 65.584819,
    longitude: 22.154984,
    event_start: new Date(Date.now() + 3600000 * 5).toISOString(),
    event_end: new Date(Date.now() + 3600000 * 10).toISOString(),
    attendees_count: 23,
    groups_count: 4,
  };

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

  const handleJoinGroup = (type: 'create' | 'browse') => {
    setShowJoinModal(false);
    toast({
      title: type === 'create' ? "Group created!" : "Joined group!",
      description: `You've ${type === 'create' ? 'created a new' : 'joined an existing'} group for this event`,
    });
  };

  return (
    <div className="min-h-[calc(100dvh-8rem)] md:min-h-[calc(100dvh-4rem)]">
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
              <span className="font-medium">{event.attendees_count} going</span>
            </div>
            <div className="flex items-center gap-2">
              <UserPlus className="w-4 h-4 text-primary" />
              <span className="font-medium">{event.groups_count} groups</span>
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="md:col-span-2 space-y-6">
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
            <Card>
              <CardHeader>
                <CardTitle>Location</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="h-[300px] rounded-b-lg overflow-hidden">
                  <MapContainer
                    center={[event.latitude, event.longitude]}
                    zoom={15}
                    className="h-full w-full"
                    style={{ zIndex: 0 }}
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <Marker position={[event.latitude, event.longitude]}>
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
                        onClick={() => window.open(`https://maps.google.com/?q=${event.latitude},${event.longitude}`, '_blank')}
                      >
                        Open in Google Maps →
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
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
                        {formatTime(event.event_start)} - {formatTime(event.event_end)}
                      </p>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Action Buttons */}
                <div className="space-y-2">
                  <Dialog open={showJoinModal} onOpenChange={setShowJoinModal}>
                    <DialogTrigger asChild>
                      <Button className="w-full" size="lg">
                        <UserPlus className="w-4 h-4 mr-2" />
                        Join Event
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Join {event.name}</DialogTitle>
                        <DialogDescription>
                          Choose how you want to participate in this event
                        </DialogDescription>
                      </DialogHeader>
                      <div className="space-y-3 mt-4">
                        <Button 
                          variant="default" 
                          className="w-full justify-start h-auto py-4"
                          onClick={() => handleJoinGroup('create')}
                        >
                          <div className="text-left">
                            <div className="font-semibold mb-1">Create New Group</div>
                            <div className="text-xs text-muted-foreground font-normal">
                              Start your own group and invite friends
                            </div>
                          </div>
                        </Button>
                        <Button 
                          variant="outline" 
                          className="w-full justify-start h-auto py-4"
                          onClick={() => handleJoinGroup('browse')}
                        >
                          <div className="text-left">
                            <div className="font-semibold mb-1">Join Existing Group</div>
                            <div className="text-xs text-muted-foreground font-normal">
                              Browse {event.groups_count} groups looking for members
                            </div>
                          </div>
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog>

                  <Button variant="outline" className="w-full" onClick={handleShare}>
                    <Share2 className="w-4 h-4 mr-2" />
                    Share Event
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Attendees Preview */}
            <Card>
              <CardHeader>
                <CardTitle>Who's Going</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2 mb-3">
                  <div className="flex -space-x-2">
                    {[1, 2, 3, 4].map((i) => (
                      <div
                        key={i}
                        className="w-8 h-8 rounded-full bg-primary/10 border-2 border-background flex items-center justify-center text-xs font-medium"
                      >
                        {String.fromCharCode(65 + i)}
                      </div>
                    ))}
                  </div>
                  <span className="text-sm text-muted-foreground">
                    +{event.attendees_count - 4} others
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Join them and make new friends!
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
