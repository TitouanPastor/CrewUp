import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Icon } from 'leaflet';
import { Calendar, MapPin, Users, Map, List } from 'lucide-react';
import { Event } from '../types';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
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
    id: 1,
    creator_id: 1,
    name: 'Friday Night at Bishops Arms',
    description: 'Weekly student party with special drinks and great music!',
    event_type: 'bar',
    address: 'Storgatan 15, Luleå',
    latitude: 65.584819,
    longitude: 22.154984,
    event_start: new Date(Date.now() + 3600000 * 5).toISOString(),
    created_at: new Date().toISOString(),
    attendees_count: 23,
    groups_count: 4,
  },
  {
    id: 2,
    creator_id: 2,
    name: 'Live Music Night',
    description: 'Local bands playing all night long!',
    event_type: 'concert',
    address: 'Kulturens Hus, Luleå',
    latitude: 65.5842,
    longitude: 22.1567,
    event_start: new Date(Date.now() + 3600000 * 24).toISOString(),
    created_at: new Date().toISOString(),
    attendees_count: 45,
    groups_count: 7,
  },
  {
    id: 3,
    creator_id: 1,
    name: 'Karaoke Night',
    description: 'Sing your heart out with friends!',
    event_type: 'bar',
    address: 'Downtown Luleå',
    latitude: 65.583,
    longitude: 22.153,
    event_start: new Date(Date.now() + 3600000 * 48).toISOString(),
    created_at: new Date().toISOString(),
    attendees_count: 12,
    groups_count: 2,
  },
];

export default function HomePage() {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<'map' | 'list'>('map');

  const handleEventClick = (eventId: number) => {
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
    <div className="h-[calc(100vh-4rem)] md:h-[calc(100vh-4rem)]">
      {/* Mobile: Toggle buttons */}
      <div className="md:hidden bg-white border-b border-gray-200 px-4 py-3 flex gap-2">
        <Button
          variant={viewMode === 'map' ? 'primary' : 'secondary'}
          onClick={() => setViewMode('map')}
          size="sm"
          className="flex-1"
        >
          <Map className="w-4 h-4" />
          Map
        </Button>
        <Button
          variant={viewMode === 'list' ? 'primary' : 'secondary'}
          onClick={() => setViewMode('list')}
          size="sm"
          className="flex-1"
        >
          <List className="w-4 h-4" />
          List
        </Button>
      </div>

      <div className="h-full flex">
        {/* Desktop: List on left, Map on right */}
        {/* Mobile: Toggle between map and list */}
        
        {/* Events List */}
        <div className={`
          ${viewMode === 'list' ? 'block' : 'hidden'}
          md:block
          w-full md:w-2/5 lg:w-1/3
          h-full overflow-y-auto
          bg-gray-50
        `}>
          <div className="p-4 space-y-3">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Events Near You
            </h2>
            
            {mockEvents.map((event) => (
              <Card
                key={event.id}
                onClick={() => handleEventClick(event.id)}
                className="hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="space-y-3">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {event.name}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                      {event.description}
                    </p>
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-gray-700">
                      <Calendar className="w-4 h-4 text-primary-600" />
                      <span className="font-medium">{formatDate(event.event_start)}</span>
                    </div>
                    
                    <div className="flex items-center gap-2 text-gray-700">
                      <MapPin className="w-4 h-4 text-primary-600" />
                      <span>{event.address}</span>
                    </div>

                    <div className="flex items-center gap-2 text-gray-700">
                      <Users className="w-4 h-4 text-primary-600" />
                      <span>{event.attendees_count} going · {event.groups_count} groups</span>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-gray-100">
                    <span className="inline-block px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-xs font-medium">
                      {event.event_type}
                    </span>
                  </div>
                </div>
              </Card>
            ))}
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
                position={[event.latitude || 0, event.longitude || 0]}
              >
                <Popup>
                  <div className="p-2 min-w-[200px]">
                    <h3 className="font-bold text-gray-900 mb-2">{event.name}</h3>
                    <p className="text-sm text-gray-600 mb-2">{event.address}</p>
                    <button
                      onClick={() => handleEventClick(event.id)}
                      className="text-sm text-primary-600 font-semibold hover:text-primary-700"
                    >
                      View Details →
                    </button>
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
