import { useState, useEffect } from 'react';
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
import { eventService } from '@/services/eventService';
import { useToast } from '@/hooks/use-toast';
import CreateEventDialog from '@/components/CreateEventDialog';
import { Plus } from 'lucide-react';

const eventTypes = [
  { value: 'all', label: 'All Types' },
  { value: 'bar', label: 'Bar' },
  { value: 'club', label: 'Club' },
  { value: 'concert', label: 'Concert' },
  { value: 'party', label: 'Party' },
  { value: 'restaurant', label: 'Restaurant' },
  { value: 'outdoor', label: 'Outdoor' },
  { value: 'sports', label: 'Sports' },
  { value: 'other', label: 'Other' },
];

export default function EventsPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [showCreateEvent, setShowCreateEvent] = useState(false);

  useEffect(() => {
    loadEvents();
  }, [selectedType]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const params: any = {
        limit: 100,
      };

      if (selectedType !== 'all') {
        params.event_type = selectedType;
      }

      const data = await eventService.listEvents(params);
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

  const handleEventCreated = () => {
    loadEvents();
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

  // Filter and sort events
  const filteredEvents = events
    .filter((event) => {
      const matchesSearch = event.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           (event.description?.toLowerCase() || '').includes(searchQuery.toLowerCase()) ||
                           (event.address?.toLowerCase() || '').includes(searchQuery.toLowerCase());
      return matchesSearch;
    })
    .sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(a.event_start).getTime() - new Date(b.event_start).getTime();
      } else if (sortBy === 'popular') {
        return (b.participant_count || 0) - (a.participant_count || 0);
      }
      return 0;
    });

  return (
    <div>
      <div className="max-w-7xl mx-auto px-4 md:px-6 py-6 space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-2">
              Discover Events
            </h1>
            <p className="text-muted-foreground">
              Find and join events happening around you
            </p>
          </div>
          <Button onClick={() => setShowCreateEvent(true)} className="gap-2">
            <Plus className="w-4 h-4" />
            <span className="hidden sm:inline">Create Event</span>
          </Button>
        </div>

        {/* Search and Filters */}
        <div className="space-y-4">
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
        <div>
          <p className="text-sm text-muted-foreground">
            {filteredEvents.length} {filteredEvents.length === 1 ? 'event' : 'events'} found
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-16">
            <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-sm text-muted-foreground">Loading events...</p>
          </div>
        )}

        {/* Events Grid */}
        {!loading && (
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
                      {event.participant_count} going{event.interested_count > 0 && ` · ${event.interested_count} interested`}
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
        )}

        {/* Empty State */}
        {!loading && filteredEvents.length === 0 && (
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

      {/* Create Event Dialog */}
      <CreateEventDialog
        open={showCreateEvent}
        onOpenChange={setShowCreateEvent}
        onEventCreated={handleEventCreated}
      />
    </div>
  );
}
