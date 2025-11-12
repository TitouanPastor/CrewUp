import { useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  User, 
  Mail, 
  Edit2, 
  Save, 
  X, 
  Star, 
  LogOut, 
  Calendar, 
  Users, 
  Award,
  Moon,
  Sun,
  Monitor
} from 'lucide-react';
import { useTheme } from 'next-themes';
import { Textarea } from '@/components/ui/textarea';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/hooks/use-toast';

export default function ProfilePage() {
  const { user, logout } = useAuthStore();
  const { theme, setTheme } = useTheme();
  const { toast } = useToast();
  const [isEditing, setIsEditing] = useState(false);
  const [bio, setBio] = useState(user?.bio || '');

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100dvh-8rem)]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  const handleSave = () => {
    // TODO: API call
    console.log('Saving:', { bio });
    setIsEditing(false);
    toast({
      title: "Profile updated",
      description: "Your changes have been saved successfully",
    });
  };

  const handleLogout = () => {
    logout();
    toast({
      title: "Logged out",
      description: "See you next time!",
    });
  };

  const avatarColor = `hsl(${(user.email.charCodeAt(0) * 137.5) % 360}, 70%, 50%)`;

  return (
    <div className="min-h-[calc(100dvh-8rem)] md:min-h-[calc(100dvh-4rem)]">
      <div className="max-w-5xl mx-auto px-4 md:px-6 py-6 space-y-6">
        {/* Header Card */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row md:items-start gap-6">
              {/* Avatar */}
              <Avatar className="w-24 h-24 shadow-lg">
                <AvatarFallback 
                  className="text-3xl font-bold text-white"
                  style={{ backgroundColor: avatarColor }}
                >
                  {user.first_name[0]}{user.last_name[0]}
                </AvatarFallback>
              </Avatar>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <h1 className="text-2xl md:text-3xl font-bold tracking-tight truncate">
                      {user.first_name} {user.last_name}
                    </h1>
                    <div className="flex items-center gap-2 mt-2 text-muted-foreground">
                      <Mail className="w-4 h-4 flex-shrink-0" />
                      <span className="text-sm truncate">{user.email}</span>
                    </div>
                  </div>
                  
                  <div className="flex gap-2 flex-shrink-0">
                    {!isEditing ? (
                      <Button onClick={() => setIsEditing(true)} variant="outline" size="sm">
                        <Edit2 className="w-4 h-4 mr-2" />
                        Edit
                      </Button>
                    ) : (
                      <>
                        <Button onClick={handleSave} size="sm">
                          <Save className="w-4 h-4 mr-2" />
                          Save
                        </Button>
                        <Button onClick={() => setIsEditing(false)} variant="outline" size="sm">
                          <X className="w-4 h-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
                
                {user.reputation && (
                  <div className="flex items-center gap-2 mt-4">
                    <div className="flex items-center gap-1 bg-yellow-500/10 text-yellow-700 dark:text-yellow-500 px-3 py-1.5 rounded-full">
                      <Star className="w-4 h-4 fill-current" />
                      <span className="text-sm font-semibold">
                        {user.reputation.average_rating.toFixed(1)}
                      </span>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {user.reputation.total_reviews} {user.reputation.total_reviews === 1 ? 'review' : 'reviews'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="md:col-span-2 space-y-6">
            {/* Bio Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="w-5 h-5 text-primary" />
                  About Me
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isEditing ? (
                  <Textarea
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    rows={4}
                    placeholder="Tell us about yourself..."
                    className="resize-none"
                  />
                ) : (
                  <p className="text-muted-foreground whitespace-pre-wrap">
                    {user.bio || 'No bio yet. Click "Edit" to add one!'}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Your latest events and interactions</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {[
                  {
                    type: 'event',
                    text: 'Attended Friday Night at Bishops Arms',
                    time: '2 days ago',
                    color: 'bg-primary'
                  },
                  {
                    type: 'group',
                    text: 'Joined Party Crew group',
                    time: '5 days ago',
                    color: 'bg-primary'
                  },
                  {
                    type: 'rating',
                    text: 'Received 5⭐ rating',
                    time: '1 week ago',
                    color: 'bg-yellow-500'
                  }
                ].map((activity, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors">
                    <div className={`w-2 h-2 ${activity.color} rounded-full mt-2 flex-shrink-0`}></div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium">{activity.text}</p>
                      <p className="text-sm text-muted-foreground mt-0.5">{activity.time}</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Your Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Calendar className="w-4 h-4" />
                    <span className="text-sm">Events</span>
                  </div>
                  <Badge variant="secondary" className="text-base font-semibold">12</Badge>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Users className="w-4 h-4" />
                    <span className="text-sm">Groups</span>
                  </div>
                  <Badge variant="secondary" className="text-base font-semibold">5</Badge>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Award className="w-4 h-4" />
                    <span className="text-sm">Friends</span>
                  </div>
                  <Badge variant="secondary" className="text-base font-semibold">8</Badge>
                </div>
              </CardContent>
            </Card>

            {/* Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Theme Toggle */}
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Theme</span>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="outline" size="sm" className="w-[110px] justify-between">
                        {theme === 'light' && <><Sun className="w-4 h-4 mr-2" /> Light</>}
                        {theme === 'dark' && <><Moon className="w-4 h-4 mr-2" /> Dark</>}
                        {theme === 'system' && <><Monitor className="w-4 h-4 mr-2" /> System</>}
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Appearance</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => setTheme('light')}>
                        <Sun className="w-4 h-4 mr-2" />
                        Light
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => setTheme('dark')}>
                        <Moon className="w-4 h-4 mr-2" />
                        Dark
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => setTheme('system')}>
                        <Monitor className="w-4 h-4 mr-2" />
                        System
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                <Separator />

                {/* Logout */}
                <Button 
                  onClick={handleLogout} 
                  variant="outline" 
                  className="w-full justify-start text-destructive hover:text-destructive hover:bg-destructive/10"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
