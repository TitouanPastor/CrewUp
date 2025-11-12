import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, MapPin, Users, Search, SlidersHorizontal } from 'lucide-react';
import { Event } from '../types';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

// Mock events avec plus de données
const mockEvents: Event[] = [
  {
    id: 1,
    creator_id: 1,
    name: 'Friday Night at Bishops Arms',
    description: 'Weekly student party with special drinks and great music! Join us for an unforgettable night.',
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
    description: 'Local bands playing all night long! Rock, indie, and electronic music.',
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
    description: 'Sing your heart out with friends! All genres welcome.',
    event_type: 'bar',
    address: 'Downtown Luleå',
    latitude: 65.583,
    longitude: 22.153,
    event_start: new Date(Date.now() + 3600000 * 48).toISOString(),
    created_at: new Date().toISOString(),
    attendees_count: 12,
    groups_count: 2,
  },
  {
    id: 4,
    creator_id: 3,
    name: 'Tech Meetup & Networking',
    description: 'Connect with local developers and tech enthusiasts over drinks.',
    event_type: 'other',
    address: 'LTU Campus, Luleå',
    latitude: 65.617,
    longitude: 22.142,
    event_start: new Date(Date.now() + 3600000 * 72).toISOString(),
    created_at: new Date().toISOString(),
    attendees_count: 18,
    groups_count: 3,
  },
  {
    id: 5,
    creator_id: 2,
    name: 'Saturday Night Club',
    description: 'Dance the night away with the best DJs in town!',
    event_type: 'club',
    address: 'City Center, Luleå',
    latitude: 65.585,
    longitude: 22.156,
    event_start: new Date(Date.now() + 3600000 * 96).toISOString(),
    created_at: new Date().toISOString(),
    attendees_count: 67,
    groups_count: 12,
  },
];

const eventTypes = [
  { value: 'all', label: 'All Types' },
  { value: 'bar', label: 'Bar' },
  { value: 'club', label: 'Club' },
  { value: 'concert', label: 'Concert' },
  { value: 'other', label: 'Other' },
];

export default function EventsPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [sortBy, setSortBy] = useState('date');

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Filter and sort events
  const filteredEvents = mockEvents
    .filter((event) => {
      const matchesSearch = event.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           (event.description?.toLowerCase() || '').includes(searchQuery.toLowerCase());
      const matchesType = selectedType === 'all' || event.event_type === selectedType;
      return matchesSearch && matchesType;
    })
    .sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(a.event_start).getTime() - new Date(b.event_start).getTime();
      } else if (sortBy === 'popular') {
        return (b.attendees_count || 0) - (a.attendees_count || 0);
      }
      return 0;
    });

  return (
    <div className="min-h-[calc(100dvh-8rem)] md:min-h-[calc(100dvh-4rem)]">
      <div className="max-w-7xl mx-auto px-4 md:px-6 py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-2">
            Discover Events
          </h1>
          <p className="text-muted-foreground">
            Find and join events happening around you
          </p>
        </div>

        {/* Search and Filters */}
        <div className="mb-6 space-y-4">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search events..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 h-11"
            />
          </div>

          {/* Filters Row */}
          <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-hide">
            {/* Event Type Filter - Desktop */}
            <div className="hidden md:block min-w-[200px]">
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger className="h-10">
                  <SelectValue placeholder="Event type" />
                </SelectTrigger>
                <SelectContent>
                  {eventTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Sort By - Desktop */}
            <div className="hidden md:block min-w-[200px]">
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="h-10">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="date">Soonest First</SelectItem>
                  <SelectItem value="popular">Most Popular</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Mobile Filters Sheet */}
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" className="md:hidden gap-2">
                  <SlidersHorizontal className="w-4 h-4" />
                  Filters
                </Button>
              </SheetTrigger>
              <SheetContent side="bottom" className="h-[400px]">
                <SheetHeader>
                  <SheetTitle>Filters</SheetTitle>
                  <SheetDescription>
                    Refine your event search
                  </SheetDescription>
                </SheetHeader>
                <div className="mt-6 space-y-6">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Event Type</label>
                    <Select value={selectedType} onValueChange={setSelectedType}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {eventTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Sort By</label>
                    <Select value={sortBy} onValueChange={setSortBy}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="date">Soonest First</SelectItem>
                        <SelectItem value="popular">Most Popular</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </SheetContent>
            </Sheet>

            {/* Active Filters Badge */}
            {selectedType !== 'all' && (
              <Badge variant="secondary" className="capitalize">
                {selectedType}
              </Badge>
            )}
          </div>
        </div>

        {/* Results Count */}
        <div className="mb-4">
          <p className="text-sm text-muted-foreground">
            {filteredEvents.length} {filteredEvents.length === 1 ? 'event' : 'events'} found
          </p>
        </div>

        {/* Events Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          {filteredEvents.map((event) => (
            <Card
              key={event.id}
              onClick={() => navigate(`/events/${event.id}`)}
              className="hover:shadow-lg hover:border-primary/50 transition-all cursor-pointer overflow-hidden group"
            >
              <CardContent className="p-5 space-y-4">
                <div>
                  <h3 className="text-lg font-semibold mb-2 group-hover:text-primary transition-colors line-clamp-1">
                    {event.name}
                  </h3>
                  <p className="text-sm text-muted-foreground line-clamp-2 min-h-[2.5rem]">
                    {event.description}
                  </p>
                </div>

                <div className="space-y-2.5 text-sm">
                  <div className="flex items-center gap-2.5">
                    <Calendar className="w-4 h-4 text-primary flex-shrink-0" />
                    <span className="font-medium">{formatDate(event.event_start)}</span>
                  </div>
                  
                  <div className="flex items-center gap-2.5">
                    <MapPin className="w-4 h-4 text-primary flex-shrink-0" />
                    <span className="text-muted-foreground line-clamp-1">{event.address}</span>
                  </div>

                  <div className="flex items-center gap-2.5">
                    <Users className="w-4 h-4 text-primary flex-shrink-0" />
                    <span className="text-muted-foreground">
                      {event.attendees_count} going · {event.groups_count} groups
                    </span>
                  </div>
                </div>

                <div className="pt-3 border-t border-border flex items-center justify-between">
                  <Badge variant="secondary" className="capitalize">
                    {event.event_type}
                  </Badge>
                  <Button 
                    size="sm" 
                    variant="ghost"
                    className="group-hover:bg-primary group-hover:text-primary-foreground transition-colors"
                  >
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Empty State */}
        {filteredEvents.length === 0 && (
          <div className="text-center py-16">
            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <Calendar className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No events found</h3>
            <p className="text-sm text-muted-foreground mb-6">
              Try adjusting your search or filters
            </p>
            <Button 
              variant="outline" 
              onClick={() => {
                setSearchQuery('');
                setSelectedType('all');
              }}
            >
              Clear Filters
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
