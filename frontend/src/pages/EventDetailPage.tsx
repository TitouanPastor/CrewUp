import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Calendar, MapPin, Users, ArrowLeft } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';

export default function EventDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [showJoinModal, setShowJoinModal] = useState(false);

  // Mock event data
  const event = {
    id: Number(id),
    name: 'Friday Night at Bishops Arms',
    description: 'Join us for an amazing Friday night! Great music, drinks, and vibes. Perfect opportunity to meet new people and have fun. DJ starts at 10 PM.',
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

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-6 space-y-4">
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
      >
        <ArrowLeft className="w-5 h-5" />
        <span className="font-medium">Back to Events</span>
      </button>

      {/* Main Info */}
      <Card>
        <div className="space-y-4">
          <div>
            <span className="inline-block px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm font-medium mb-3">
              {event.event_type}
            </span>
            <h1 className="text-3xl font-bold text-gray-900">
              {event.name}
            </h1>
          </div>

          <p className="text-gray-700 text-lg leading-relaxed">
            {event.description}
          </p>
        </div>
      </Card>

      {/* Details */}
      <Card>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Event Details</h2>
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <Calendar className="w-5 h-5 text-primary-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-semibold text-gray-900">{formatDate(event.event_start)}</p>
              <p className="text-sm text-gray-600">
                {formatTime(event.event_start)} - {formatTime(event.event_end)}
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <MapPin className="w-5 h-5 text-primary-600 mt-0.5 flex-shrink-0" />
            <p className="text-gray-900">{event.address}</p>
          </div>

          <div className="flex items-start gap-3">
            <Users className="w-5 h-5 text-primary-600 mt-0.5 flex-shrink-0" />
            <p className="text-gray-900">
              {event.attendees_count} people going · {event.groups_count} groups formed
            </p>
          </div>
        </div>
      </Card>

      {/* Actions */}
      <div className="flex gap-3">
        <Button variant="primary" className="flex-1" onClick={() => setShowJoinModal(true)}>
          Join Event
        </Button>
        <Button variant="secondary" className="flex-1">
          Share
        </Button>
      </div>

      {/* Join Modal */}
      <Modal isOpen={showJoinModal} onClose={() => setShowJoinModal(false)} title="Join Event">
        <div className="space-y-4">
          <p className="text-gray-700">Choose how you want to join this event:</p>
          <Button variant="primary" className="w-full">
            Create New Group
          </Button>
          <Button variant="secondary" className="w-full">
            Browse Existing Groups
          </Button>
        </div>
      </Modal>
    </div>
  );
}
