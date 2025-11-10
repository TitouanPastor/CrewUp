import { useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { User, Mail, Edit2, Save, X, Star } from 'lucide-react';

export default function ProfilePage() {
  const { user } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [bio, setBio] = useState(user?.bio || '');

  if (!user) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  const handleSave = () => {
    // TODO: API call
    console.log('Saving:', { bio });
    setIsEditing(false);
  };

  const avatarColor = `hsl(${(user.email.charCodeAt(0) * 137.5) % 360}, 70%, 50%)`;

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-6 space-y-4">
      {/* Header Card */}
      <Card>
        <div className="flex flex-col md:flex-row md:items-center gap-6">
          {/* Avatar */}
          <div 
            className="w-24 h-24 rounded-full flex items-center justify-center text-white text-3xl font-bold shadow-lg flex-shrink-0"
            style={{ backgroundColor: avatarColor }}
          >
            {user.first_name[0]}{user.last_name[0]}
          </div>
          
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900">
              {user.first_name} {user.last_name}
            </h1>
            <div className="flex items-center gap-2 mt-2 text-gray-600">
              <Mail className="w-4 h-4" />
              <span>{user.email}</span>
            </div>
            
            {user.reputation && (
              <div className="flex items-center gap-2 mt-3">
                <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
                <span className="text-lg font-semibold text-gray-900">
                  {user.reputation.average_rating.toFixed(1)}
                </span>
                <span className="text-sm text-gray-600">
                  ({user.reputation.total_reviews} reviews)
                </span>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            {!isEditing ? (
              <Button onClick={() => setIsEditing(true)} variant="secondary">
                <Edit2 className="w-4 h-4" />
                Edit
              </Button>
            ) : (
              <>
                <Button onClick={handleSave} variant="primary">
                  <Save className="w-4 h-4" />
                  Save
                </Button>
                <Button onClick={() => setIsEditing(false)} variant="ghost">
                  <X className="w-4 h-4" />
                </Button>
              </>
            )}
          </div>
        </div>
      </Card>

      {/* Bio Section */}
      <Card>
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <User className="w-5 h-5 text-primary-600" />
          About Me
        </h2>
        {isEditing ? (
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200 placeholder:text-gray-400"
            rows={4}
            placeholder="Tell us about yourself..."
          />
        ) : (
          <p className="text-gray-700 whitespace-pre-wrap">
            {user.bio || 'No bio yet. Click "Edit" to add one!'}
          </p>
        )}
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <div className="text-center">
            <p className="text-3xl font-bold text-primary-600">12</p>
            <p className="text-sm text-gray-600 mt-1">Events Attended</p>
          </div>
        </Card>
        
        <Card>
          <div className="text-center">
            <p className="text-3xl font-bold text-primary-600">5</p>
            <p className="text-sm text-gray-600 mt-1">Groups Joined</p>
          </div>
        </Card>
        
        <Card>
          <div className="text-center">
            <p className="text-3xl font-bold text-primary-600">8</p>
            <p className="text-sm text-gray-600 mt-1">Friends Made</p>
          </div>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
            <div className="w-2 h-2 bg-primary-600 rounded-full mt-2"></div>
            <div className="flex-1">
              <p className="text-gray-900 font-medium">Attended Friday Night at Bishops Arms</p>
              <p className="text-sm text-gray-600 mt-1">2 days ago</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
            <div className="w-2 h-2 bg-primary-600 rounded-full mt-2"></div>
            <div className="flex-1">
              <p className="text-gray-900 font-medium">Joined Party Crew group</p>
              <p className="text-sm text-gray-600 mt-1">5 days ago</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
            <div className="w-2 h-2 bg-green-600 rounded-full mt-2"></div>
            <div className="flex-1">
              <p className="text-gray-900 font-medium">Received 5⭐ rating</p>
              <p className="text-sm text-gray-600 mt-1">1 week ago</p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
