import { useNavigate } from 'react-router-dom';
import { Calendar, Users } from 'lucide-react';
import Card from '../components/ui/Card';

const mockGroups = [
  { id: 1, name: 'Party Crew', event_name: 'Friday Night Party', members: 5 },
  { id: 2, name: 'Music Lovers', event_name: 'Live Concert', members: 8 },
];

export default function EventsPage() {
  const navigate = useNavigate();

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">
          My Groups
        </h1>
        <p className="text-gray-600 mt-2">Groups you've joined for upcoming events</p>
      </div>

      <div className="space-y-4">
        {mockGroups.map((group) => (
          <Card
            key={group.id}
            onClick={() => navigate(`/groups/${group.id}`)}
            className="hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900">
                  {group.name}
                </h3>
                <div className="flex items-center gap-2 mt-2 text-gray-600">
                  <Calendar className="w-4 h-4 text-primary-600" />
                  <span className="text-sm">{group.event_name}</span>
                </div>
                <div className="flex items-center gap-2 mt-1 text-gray-600">
                  <Users className="w-4 h-4 text-primary-600" />
                  <span className="text-sm">{group.members} members</span>
                </div>
              </div>
              
              <div className="ml-4">
                <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
                  <Users className="w-8 h-8 text-primary-600" />
                </div>
              </div>
            </div>
          </Card>
        ))}

        {mockGroups.length === 0 && (
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600">No groups yet</p>
            <p className="text-sm text-gray-500 mt-1">Join an event to create or join a group</p>
          </div>
        )}
      </div>
    </div>
  );
}
