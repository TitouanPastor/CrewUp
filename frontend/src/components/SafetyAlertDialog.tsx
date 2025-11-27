import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  AlertTriangle, 
  Heart, 
  ShieldAlert, 
  HelpCircle,
  Loader2,
  MapPin,
  Clock,
} from 'lucide-react';
import { safetyService, type CreateAlertData } from '@/services/safetyService';
import { eventService } from '@/services/eventService';
import { groupService, type Group } from '@/services/groupService';
import { extractErrorMessage } from '@/utils/errorHandler';
import { useToast } from '@/hooks/use-toast';
import keycloak from '@/keycloak';
import type { Event } from '@/types';

interface SafetyAlertDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAlertSent?: () => void;
  onActiveEventsChange?: (hasActiveEvents: boolean) => void;
}

interface ActiveEventWithGroups extends Event {
  groups: Group[];
}

const ALERT_TYPES = [
  { 
    value: 'help' as const, 
    label: 'Help Needed', 
    icon: HelpCircle,
    description: 'General assistance required',
    color: 'text-orange-500'
  },
  { 
    value: 'medical' as const, 
    label: 'Medical Emergency', 
    icon: Heart,
    description: 'Medical attention needed',
    color: 'text-red-500'
  },
  { 
    value: 'harassment' as const, 
    label: 'Harassment/Safety', 
    icon: ShieldAlert,
    description: 'Feeling unsafe or harassed',
    color: 'text-purple-500'
  },
  { 
    value: 'other' as const, 
    label: 'Other', 
    icon: AlertTriangle,
    description: 'Other emergency situation',
    color: 'text-yellow-500'
  },
] as const;

const DEFAULT_MESSAGE = "Emergency - need help!";

export default function SafetyAlertDialog({
  open,
  onOpenChange,
  onAlertSent,
  onActiveEventsChange,
}: SafetyAlertDialogProps) {
  const { toast } = useToast();
  
  // State
  const [alertType, setAlertType] = useState<'help' | 'medical' | 'harassment' | 'other'>('help');
  const [message, setMessage] = useState(DEFAULT_MESSAGE);
  const [activeEvents, setActiveEvents] = useState<ActiveEventWithGroups[]>([]);
  const [selectedGroups, setSelectedGroups] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [fetchingEvents, setFetchingEvents] = useState(true);
  const [autoSendTimer, setAutoSendTimer] = useState<NodeJS.Timeout | null>(null);
  const [countdown, setCountdown] = useState(5);
  const [userInteracted, setUserInteracted] = useState(false);
  const [isSending, setIsSending] = useState(false); // Prevent duplicate sends

  // Load active events and their groups when dialog opens
  useEffect(() => {
    if (open) {
      loadActiveEvents();
      resetDialog();
    } else {
      // Clear timer when dialog closes
      if (autoSendTimer) {
        clearInterval(autoSendTimer);
        setAutoSendTimer(null);
      }
    }
  }, [open]);

  // Auto-send countdown
  useEffect(() => {
    // Don't start timer if:
    // - Dialog is closed
    // - User already interacted
    // - No active events
    // - Timer already running
    if (!open || userInteracted || activeEvents.length === 0 || autoSendTimer) return;

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          // Stop the timer first
          clearInterval(timer);
          setAutoSendTimer(null);
          
          // Auto-send the alert (only if groups are selected)
          if (selectedGroups.size > 0) {
            handleSendAlert();
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    setAutoSendTimer(timer);

    return () => {
      clearInterval(timer);
    };
  }, [open, userInteracted, activeEvents.length]); // Removed selectedGroups.size dependency

  const resetDialog = () => {
    setAlertType('help');
    setMessage(DEFAULT_MESSAGE);
    setSelectedGroups(new Set());
    setUserInteracted(false);
    setCountdown(5);
    setIsSending(false);
  };

  const handleUserInteraction = () => {
    if (!userInteracted) {
      setUserInteracted(true);
      if (autoSendTimer) {
        clearInterval(autoSendTimer);
        setAutoSendTimer(null);
      }
    }
  };

  const loadActiveEvents = async () => {
    try {
      setFetchingEvents(true);
      
      // Get current user ID
      const currentUserId = keycloak.tokenParsed?.sub;
      if (!currentUserId) {
        console.error('No user ID available');
        setFetchingEvents(false);
        return;
      }
      
      // Get events where user is going (ongoing and upcoming, not past)
      const { events } = await eventService.listEvents({
        status: 'going',
        limit: 50,
        include_ongoing: true,   // Include ongoing events
        include_past: false,     // Exclude finished events
      });

      // Filter for currently active events with 2-hour margin (same as backend)
      // Event is "active" from 2h before start to 2h after end
      const now = new Date();
      const MARGIN_MS = 2 * 60 * 60 * 1000; // 2 hours in milliseconds (aligned with backend)
      
      const active = events.filter((event) => {
        const start = new Date(event.event_start);
        const end = event.event_end ? new Date(event.event_end) : new Date(start.getTime() + 24 * 60 * 60 * 1000); // Default 24h if no end
        
        const activeStart = new Date(start.getTime() - MARGIN_MS); // 2h before
        const activeEnd = new Date(end.getTime() + MARGIN_MS); // 2h after
        
        return activeStart <= now && now <= activeEnd && !event.is_cancelled;
      });

      console.log('Active events found:', active.length, active);

      // Load groups for each active event
      const eventsWithGroups = await Promise.all(
        active.map(async (event) => {
          const { groups } = await groupService.listGroups(event.id);
          console.log(`Groups for event ${event.name}:`, groups);
          
          // Filter groups where current user is a member
          const userGroups: typeof groups = [];
          for (const group of groups) {
            try {
              const { members } = await groupService.getMembers(group.id);
              console.log(`Members of group ${group.name}:`, members);
              
              // Check if current user is in the members list
              const isMember = members.some((m: any) => m.keycloak_id === currentUserId);
              console.log(`Is user member of ${group.name}?`, isMember);
              
              if (isMember) {
                userGroups.push(group);
              }
            } catch (error) {
              console.error(`Failed to get members for group ${group.id}:`, error);
              // Skip groups we can't access
            }
          }
          return {
            ...event,
            groups: userGroups,
          };
        })
      );

      const eventsWithUserGroups = eventsWithGroups.filter(e => e.groups.length > 0);
      console.log('Events with user groups:', eventsWithUserGroups);
      
      setActiveEvents(eventsWithUserGroups);
      
      // Notify parent about active events status
      onActiveEventsChange?.(eventsWithUserGroups.length > 0);

      // Auto-select all groups by default
      const allGroupIds = new Set(eventsWithUserGroups.flatMap(e => e.groups.map(g => g.id)));
      setSelectedGroups(allGroupIds);

    } catch (error) {
      console.error('Failed to load active events:', error);
      toast({
        title: 'Error',
        description: extractErrorMessage(error),
        variant: 'destructive',
      });
    } finally {
      setFetchingEvents(false);
    }
  };

  const handleSendAlert = async () => {
    // Prevent duplicate sends
    if (isSending) {
      console.log('Alert already being sent, ignoring duplicate call');
      return;
    }
    
    if (selectedGroups.size === 0) {
      toast({
        title: 'No groups selected',
        description: 'Please select at least one group to send the alert',
        variant: 'destructive',
      });
      return;
    }

    try {
      setIsSending(true);
      setLoading(true);

      // Get current location
      const location = await safetyService.getCurrentLocation();

      // Generate a batch ID for all alerts in this group
      const batchId = crypto.randomUUID();

      // Send alert to each selected group
      const alerts = Array.from(selectedGroups).map(async (groupId) => {
        // Find the event for this group
        const event = activeEvents.find(e => e.groups.some(g => g.id === groupId));
        if (!event) return;

        const alertData: CreateAlertData = {
          event_id: event.id,
          group_id: groupId,
          batch_id: batchId,  // Link all alerts together
          alert_type: alertType,
          message: message.trim() || DEFAULT_MESSAGE,
          ...(location && {
            latitude: location.latitude,
            longitude: location.longitude,
          }),
        };

        return safetyService.createAlert(alertData);
      });

      await Promise.all(alerts);

      toast({
        title: 'Alert sent',
        description: `Emergency alert sent to ${selectedGroups.size} group(s)`,
      });

      // Dispatch event to notify navbar
      window.dispatchEvent(new CustomEvent('alert-created'));
      
      onAlertSent?.();
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to send alert:', error);
      toast({
        title: 'Failed to send alert',
        description: extractErrorMessage(error),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
      setIsSending(false);
    }
  };

  const toggleGroup = (groupId: string) => {
    handleUserInteraction();
    setSelectedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  };

  const toggleAllGroups = () => {
    handleUserInteraction();
    if (selectedGroups.size === activeEvents.flatMap(e => e.groups).length) {
      setSelectedGroups(new Set());
    } else {
      const allGroupIds = new Set(activeEvents.flatMap(e => e.groups.map(g => g.id)));
      setSelectedGroups(allGroupIds);
    }
  };

  const totalGroups = activeEvents.flatMap(e => e.groups).length;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="w-5 h-5" />
            Emergency Alert
          </DialogTitle>
          <DialogDescription>
            Send an emergency alert to your active event groups
          </DialogDescription>
        </DialogHeader>

        {!userInteracted && (
          <Alert className="bg-destructive/10 border-destructive/20">
            <Clock className="w-4 h-4 text-destructive" />
            <AlertDescription className="text-destructive font-medium">
              Auto-sending in {countdown} seconds... Click anywhere to customize
            </AlertDescription>
          </Alert>
        )}

        {fetchingEvents ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
          </div>
        ) : activeEvents.length === 0 ? (
          <Alert>
            <AlertDescription>
              You don't have any active events right now. Safety alerts can only be sent during ongoing events.
            </AlertDescription>
          </Alert>
        ) : (
          <div className="space-y-4">
            {/* Alert Type Selection */}
            <div className="space-y-2">
              <Label>Alert Type</Label>
              <div className="grid grid-cols-2 gap-2">
                {ALERT_TYPES.map((type) => {
                  const Icon = type.icon;
                  return (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => {
                        handleUserInteraction();
                        setAlertType(type.value);
                      }}
                      className={`p-3 rounded-lg border-2 transition-all text-left ${
                        alertType === type.value
                          ? 'border-destructive bg-destructive/10'
                          : 'border-border hover:border-muted-foreground'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <Icon className={`w-5 h-5 mt-0.5 ${type.color}`} />
                        <div>
                          <div className="font-medium text-sm">{type.label}</div>
                          <div className="text-xs text-muted-foreground">{type.description}</div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Message */}
            <div className="space-y-2">
              <Label htmlFor="message">Additional Details (optional)</Label>
              <Textarea
                id="message"
                placeholder={DEFAULT_MESSAGE}
                value={message}
                onChange={(e) => {
                  handleUserInteraction();
                  setMessage(e.target.value);
                }}
                rows={3}
                maxLength={500}
              />
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                Your location will be shared automatically if available
              </p>
            </div>

            {/* Group Selection */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Send to Groups ({selectedGroups.size}/{totalGroups})</Label>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={toggleAllGroups}
                  className="h-auto py-1 px-2 text-xs"
                >
                  {selectedGroups.size === totalGroups ? 'Deselect All' : 'Select All'}
                </Button>
              </div>
              <div className="space-y-3 max-h-48 overflow-y-auto">
                {activeEvents.map((event) => (
                  <div key={event.id} className="space-y-2">
                    <div className="text-sm font-medium text-muted-foreground">
                      {event.name}
                    </div>
                    {event.groups.map((group) => (
                      <div
                        key={group.id}
                        className="flex items-start gap-2 p-2 rounded-md hover:bg-accent cursor-pointer"
                        onClick={() => toggleGroup(group.id)}
                      >
                        <Checkbox
                          checked={selectedGroups.has(group.id)}
                          onCheckedChange={() => toggleGroup(group.id)}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm">{group.name}</div>
                          <div className="text-xs text-muted-foreground">
                            {group.member_count || 0} members
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              {userInteracted ? (
                <>
                  <Button
                    variant="outline"
                    onClick={() => onOpenChange(false)}
                    className="flex-1"
                    disabled={loading}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleSendAlert}
                    disabled={loading || selectedGroups.size === 0}
                    className="flex-1"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="w-4 h-4 mr-2" />
                        Send Alert
                      </>
                    )}
                  </Button>
                </>
              ) : (
                <Button
                  variant="outline"
                  onClick={handleUserInteraction}
                  className="w-full"
                >
                  Customize Alert
                </Button>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
