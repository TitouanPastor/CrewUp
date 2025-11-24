import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Icon } from 'leaflet';
import { Calendar, MapPin, Users, Map, List } from 'lucide-react';
import { Event } from '../types';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { eventService } from '@/services/eventService';
import { useToast } from '@/hooks/use-toast';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons
delete (Icon.Default.prototype as any)._getIconUrl;
Icon.Default.mergeOptions({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export default function HomePage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [viewMode, setViewMode] = useState<'map' | 'list'>('map');
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const data = await eventService.listEvents({ limit: 50 });
      setEvents(data.events);
    } catch (error) {
      console.error('Failed to load events:', error);
      toast({
        title: "Error",
        description: "Failed to load events. Please try again later.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleEventClick = (eventId: string) => {
    navigate(`/events/${eventId}`);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="h-[calc(100dvh-5rem)] md:h-[calc(100dvh-4rem)]">
      {/* Mobile: Toggle View Mode */}
      <div className="md:hidden bg-background border-b border-border px-4 py-3">
        <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'map' | 'list')} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="map" className="gap-2">
              <Map className="w-4 h-4" />
              Map
            </TabsTrigger>
            <TabsTrigger value="list" className="gap-2">
              <List className="w-4 h-4" />
              List
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="h-full flex">
        {/* Events List */}
        <div className={`
          ${viewMode === 'list' ? 'block' : 'hidden'}
          md:block
          w-full md:w-2/5 lg:w-1/3
          h-full overflow-y-auto
          bg-background
        `}>
          <div className="p-4 md:p-6 space-y-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight mb-1">
                Events Near You
              </h1>
              <p className="text-muted-foreground">
                Find your crew for tonight
              </p>
            </div>
            
            <div className="space-y-3">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : events.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-muted-foreground">No events found nearby.</p>
                  <Button
                    variant="outline"
                    onClick={() => navigate('/events')}
                    className="mt-4"
                  >
                    View All Events
                  </Button>
                </div>
              ) : (
                events.map((event) => (
                  <Card
                    key={event.id}
                    onClick={() => handleEventClick(event.id)}
                    className="hover:shadow-lg hover:border-primary/50 transition-all cursor-pointer overflow-hidden group"
                  >
                    <CardContent className="p-4 space-y-3">
                      <div>
                        <h3 className="text-lg font-semibold mb-1 group-hover:text-primary transition-colors">
                          {event.name}
                        </h3>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {event.description}
                        </p>
                      </div>

                      <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2 text-foreground">
                          <Calendar className="w-4 h-4 text-primary" />
                          <span className="font-medium">{formatDate(event.event_start)}</span>
                        </div>

                        <div className="flex items-center gap-2 text-muted-foreground">
                          <MapPin className="w-4 h-4 text-primary" />
                          <span className="line-clamp-1">{event.address}</span>
                        </div>

                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Users className="w-4 h-4 text-primary" />
                          <span>{event.participant_count} going{event.interested_count > 0 && ` · ${event.interested_count} interested`}</span>
                        </div>
                      </div>

                      <div className="pt-2 border-t border-border">
                        <Badge variant="secondary" className="capitalize">
                          {event.event_type}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Map */}
        <div className={`
          ${viewMode === 'map' ? 'block' : 'hidden'}
          md:block
          w-full md:w-3/5 lg:w-2/3
          h-full
        `}>
          <MapContainer
            center={[65.5848, 22.1547]}
            zoom={13}
            className="h-full w-full"
            style={{ zIndex: 0 }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {!loading && events
              .filter(event => event.latitude && event.longitude)
              .map((event) => (
                <Marker
                  key={event.id}
                  position={[Number(event.latitude) || 0, Number(event.longitude) || 0]}
                >
                  <Popup>
                    <div className="p-2 min-w-[200px]">
                      <h3 className="font-bold mb-2">{event.name}</h3>
                      <p className="text-sm text-muted-foreground mb-3">{event.address}</p>
                      <Button
                        size="sm"
                        onClick={() => handleEventClick(event.id)}
                        className="w-full"
                      >
                        View Details →
                      </Button>
                    </div>
                  </Popup>
                </Marker>
              ))
            }
          </MapContainer>
        </div>
      </div>
    </div>
  );
}
