import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Calendar, MapPin, Users, Heart } from 'lucide-react';
import { eventService } from '@/services/eventService';
import type { Event } from '@/types';

interface UserEventsSectionProps {
  userId: string;
}

export default function UserEventsSection({ userId }: UserEventsSectionProps) {
  const navigate = useNavigate();
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadUserEvents();
  }, [userId]);

  const loadUserEvents = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch user's created events, including cancelled and past ones
      // Set start_date_from to a past date to include past events
      const pastDate = new Date();
      pastDate.setFullYear(pastDate.getFullYear() - 1); // Go back 1 year

      const response = await eventService.listEvents({
        creator_id: userId,
        is_cancelled: true,  // Include cancelled events
        start_date_from: pastDate.toISOString(),
        limit: 20,
        offset: 0,
      });

      setEvents(response.events);
    } catch (err) {
      console.error('Failed to load user events:', err);
      setError('Failed to load events');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleEventClick = (eventId: string) => {
    navigate(`/events/${eventId}`);
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-primary" />
            My Created Events
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-primary" />
            My Created Events
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{error}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-primary" />
          My Created Events
          <Badge variant="secondary" className="ml-auto">
            {events.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {events.length === 0 ? (
          <div className="text-center py-8">
            <Calendar className="w-12 h-12 mx-auto text-muted-foreground/50 mb-3" />
            <p className="text-muted-foreground">You haven't created any events yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {events.map((event) => (
              <div
                key={event.id}
                onClick={() => handleEventClick(event.id)}
                className="p-3 md:p-4 rounded-lg border bg-card hover:bg-accent transition-colors cursor-pointer group"
              >
                <div className="space-y-2">
                  {/* Title and badges */}
                  <div className="flex items-start gap-2 flex-wrap">
                    <h3 className="font-semibold text-sm group-hover:text-primary transition-colors min-w-0 line-clamp-1 flex-1">
                      {event.name}
                    </h3>
                    <div className="flex gap-1 flex-shrink-0">
                      <Badge
                        variant="secondary"
                        className="text-xs capitalize whitespace-nowrap"
                      >
                        {event.event_type}
                      </Badge>
                      {event.is_cancelled && (
                        <Badge variant="destructive" className="text-xs whitespace-nowrap">
                          Cancelled
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Event details */}
                  <div className="space-y-1.5">
                    <div className="flex items-start gap-2 text-xs text-muted-foreground">
                      <Calendar className="w-3 h-3 flex-shrink-0 mt-0.5" />
                      <span className="break-words">{formatDate(event.event_start)} at {formatTime(event.event_start)}</span>
                    </div>

                    <div className="flex items-start gap-2 text-xs text-muted-foreground">
                      <MapPin className="w-3 h-3 flex-shrink-0 mt-0.5" />
                      <span className="break-words line-clamp-2">{event.address}</span>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
                      <div className="flex items-center gap-1 whitespace-nowrap">
                        <Users className="w-3 h-3" />
                        <span>{event.participant_count} going</span>
                      </div>
                      <div className="flex items-center gap-1 whitespace-nowrap">
                        <Heart className="w-3 h-3" />
                        <span>{event.interested_count} interested</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
