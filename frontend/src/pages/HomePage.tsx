import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Icon } from 'leaflet';
import { Calendar, MapPin, Users, Map, List } from 'lucide-react';
import { Event } from '../types';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons
delete (Icon.Default.prototype as any)._getIconUrl;
Icon.Default.mergeOptions({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Mock events
const mockEvents: Event[] = [
  {
    id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    creator_id: 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    name: 'Friday Night at Bishops Arms',
    description: 'Weekly student party with special drinks and great music!',
    event_type: 'bar',
    address: 'Storgatan 15, Luleå',
    latitude: 65.584819,
    longitude: 22.154984,
    event_start: new Date(Date.now() + 3600000 * 5).toISOString(),
    is_public: true,
    is_cancelled: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    participant_count: 23,
    interested_count: 5,
    is_full: false,
  },
  {
    id: 'a1eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    creator_id: 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    name: 'Live Music Night',
    description: 'Local bands playing all night long!',
    event_type: 'concert',
    address: 'Kulturens Hus, Luleå',
    latitude: 65.5842,
    longitude: 22.1567,
    event_start: new Date(Date.now() + 3600000 * 24).toISOString(),
    is_public: true,
    is_cancelled: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    participant_count: 45,
    interested_count: 12,
    is_full: false,
  },
  {
    id: 'a2eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    creator_id: 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    name: 'Karaoke Night',
    description: 'Sing your heart out with friends!',
    event_type: 'bar',
    address: 'Downtown Luleå',
    latitude: 65.583,
    longitude: 22.153,
    event_start: new Date(Date.now() + 3600000 * 48).toISOString(),
    is_public: true,
    is_cancelled: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    participant_count: 12,
    interested_count: 3,
    is_full: false,
  },
];

export default function HomePage() {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<'map' | 'list'>('map');

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
              {mockEvents.map((event) => (
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
              ))}
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
            {mockEvents.map((event) => (
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
            ))}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}
