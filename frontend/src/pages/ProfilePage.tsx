import { useState, useEffect } from 'react';
import { useAuthStore } from '../stores/authStore';
import { userService, type User } from '../services/userService';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  User as UserIcon, 
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
  Monitor,
  AlertCircle
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
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function ProfilePage() {
  const { logout } = useAuthStore();
  const { theme, setTheme } = useTheme();
  const { toast } = useToast();
  
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  const [bio, setBio] = useState('');
  const [interests, setInterests] = useState<string[]>([]);
  const [interestInput, setInterestInput] = useState('');

  // Load user profile on mount
  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Try to get existing profile
      try {
        const profile = await userService.getMe();
        setUser(profile);
        setBio(profile.bio || '');
        setInterests(profile.interests || []);
      } catch (err: any) {
        // If 404, create profile from Keycloak token
        if (err.response?.status === 404) {
          const newProfile = await userService.createProfile();
          setUser(newProfile);
          setBio(newProfile.bio || '');
          setInterests(newProfile.interests || []);
          toast({
            title: "Profile created",
            description: "Welcome to CrewUp!",
          });
        } else {
          throw err;
        }
      }
    } catch (err: any) {
      console.error('Failed to load profile:', err);
      setError(err.response?.data?.error?.message || 'Failed to load profile');
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load your profile. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setError(null);
      
      const updated = await userService.updateProfile({
        bio: bio.trim() || undefined,
        interests: interests.length > 0 ? interests : undefined,
      });
      
      setUser(updated);
      setIsEditing(false);
      
      toast({
        title: "Profile updated",
        description: "Your changes have been saved successfully",
      });
    } catch (err: any) {
      console.error('Failed to update profile:', err);
      const errorMsg = err.response?.data?.error?.message || 'Failed to update profile';
      setError(errorMsg);
      toast({
        variant: "destructive",
        title: "Update failed",
        description: errorMsg,
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setBio(user?.bio || '');
    setInterests(user?.interests || []);
    setInterestInput('');
    setIsEditing(false);
    setError(null);
  };

  const handleAddInterest = () => {
    const trimmed = interestInput.trim();
    if (trimmed && !interests.includes(trimmed) && interests.length < 10) {
      setInterests([...interests, trimmed]);
      setInterestInput('');
    }
  };

  const handleRemoveInterest = (interest: string) => {
    setInterests(interests.filter(i => i !== interest));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100dvh-8rem)]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading your profile...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100dvh-8rem)]">
        <Alert variant="destructive" className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error || 'Failed to load profile'}
          </AlertDescription>
          <Button onClick={loadProfile} variant="outline" size="sm" className="mt-4">
            Try again
          </Button>
        </Alert>
      </div>
    );
  }


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
        {/* Error Alert */}
        {error && !isEditing && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

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
                        <Button onClick={handleSave} size="sm" disabled={isSaving}>
                          <Save className="w-4 h-4 mr-2" />
                          {isSaving ? 'Saving...' : 'Save'}
                        </Button>
                        <Button onClick={handleCancel} variant="outline" size="sm" disabled={isSaving}>
                          <X className="w-4 h-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center gap-2 mt-4">
                  <div className="flex items-center gap-1 bg-yellow-500/10 text-yellow-700 dark:text-yellow-500 px-3 py-1.5 rounded-full">
                    <Star className="w-4 h-4 fill-current" />
                    <span className="text-sm font-semibold">
                      {(user.reputation_score || 0).toFixed(1)}
                    </span>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {user.total_ratings || 0} {user.total_ratings === 1 ? 'review' : 'reviews'}
                  </span>
                </div>
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
                  <UserIcon className="w-5 h-5 text-primary" />
                  About Me
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isEditing ? (
                  <div className="space-y-2">
                    <Textarea
                      value={bio}
                      onChange={(e) => setBio(e.target.value)}
                      rows={4}
                      placeholder="Tell us about yourself..."
                      className="resize-none"
                      maxLength={500}
                    />
                    <p className="text-xs text-muted-foreground text-right">
                      {bio.length}/500 characters
                    </p>
                  </div>
                ) : (
                  <p className="text-muted-foreground whitespace-pre-wrap">
                    {bio || 'No bio yet. Click Edit to add one!'}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Interests Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="w-5 h-5 text-primary" />
                  Interests
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isEditing ? (
                  <div className="space-y-3">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={interestInput}
                        onChange={(e) => setInterestInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleAddInterest();
                          }
                        }}
                        placeholder="Add an interest..."
                        className="flex-1 px-3 py-2 text-sm rounded-md border border-input bg-background"
                        maxLength={50}
                        disabled={interests.length >= 10}
                      />
                      <Button 
                        onClick={handleAddInterest} 
                        size="sm"
                        disabled={!interestInput.trim() || interests.length >= 10}
                      >
                        Add
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {interests.map((interest) => (
                        <Badge 
                          key={interest} 
                          variant="secondary" 
                          className="px-3 py-1 text-sm cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                          onClick={() => handleRemoveInterest(interest)}
                        >
                          {interest} <X className="w-3 h-3 ml-1" />
                        </Badge>
                      ))}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {interests.length}/10 interests • Click to remove
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {interests.length > 0 ? (
                      interests.map((interest) => (
                        <Badge key={interest} variant="secondary" className="px-3 py-1 text-sm">
                          {interest}
                        </Badge>
                      ))
                    ) : (
                      <p className="text-muted-foreground text-sm">No interests added yet</p>
                    )}
                  </div>
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
