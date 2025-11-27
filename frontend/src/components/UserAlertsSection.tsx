import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertTriangle,
  Heart,
  ShieldAlert,
  HelpCircle,
  MapPin,
  Clock,
  CheckCircle,
  Loader2,
  ExternalLink,
  Users,
} from 'lucide-react';
import { safetyService, type SafetyAlert } from '@/services/safetyService';
import { extractErrorMessage } from '@/utils/errorHandler';
import { groupService, type Group } from '@/services/groupService';
import { eventService } from '@/services/eventService';
import { useToast } from '@/hooks/use-toast';
import { formatDistanceToNow } from 'date-fns';
import { Link } from 'react-router-dom';
import type { Event } from '@/types';

const ALERT_TYPE_CONFIG = {
  help: {
    label: 'Help Needed',
    icon: HelpCircle,
    color: 'text-orange-500',
    bgColor: 'bg-orange-500/10',
  },
  medical: {
    label: 'Medical Emergency',
    icon: Heart,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
  },
  harassment: {
    label: 'Harassment',
    icon: ShieldAlert,
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
  },
  other: {
    label: 'Other',
    icon: AlertTriangle,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
  },
} as const;

type AlertType = keyof typeof ALERT_TYPE_CONFIG;

interface AlertWithDetails extends SafetyAlert {
  group?: Group;
  event?: Event;
}

interface GroupedAlert {
  id: string; // Representative alert ID
  batch_id: string;
  alert_type: AlertType;
  message: string;
  latitude: number | null;
  longitude: number | null;
  created_at: string;
  resolved_at: string | null;
  groups: Group[];
  events: Event[];
  alert_ids: string[]; // All alert IDs in this batch
}

export default function UserAlertsSection() {
  const { toast } = useToast();
  const [alerts, setAlerts] = useState<GroupedAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolvingIds, setResolvingIds] = useState<Set<string>>(new Set());
  const [showResolved, setShowResolved] = useState(false);

  useEffect(() => {
    loadAlerts();
  }, [showResolved]);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const { alerts: fetchedAlerts } = await safetyService.getMyAlerts({
        resolved: showResolved ? undefined : false,
        limit: 50,
      });
      
      // Enrich alerts with group and event data
      const enrichedAlerts: AlertWithDetails[] = await Promise.all(
        fetchedAlerts.map(async (alert) => {
          try {
            // First get the group
            const group = await groupService.getGroup(alert.group_id);
            
            // Then get the event from the group's event_id
            let event: Event | undefined;
            if (group.event_id) {
              try {
                event = await eventService.getEvent(group.event_id);
              } catch (error) {
                console.error('Failed to load event:', error);
              }
            }
            
            return { ...alert, group, event };
          } catch (error) {
            console.error('Failed to load alert details:', error);
            return alert;
          }
        })
      );

      // Group alerts by batch_id
      const batchMap = new Map<string, GroupedAlert>();
      
      enrichedAlerts.forEach((alert) => {
        const batchId = alert.batch_id || alert.id;
        
        if (!batchMap.has(batchId)) {
          batchMap.set(batchId, {
            id: alert.id,
            batch_id: batchId,
            alert_type: alert.alert_type as AlertType,
            message: alert.message || '',
            latitude: alert.latitude ?? null,
            longitude: alert.longitude ?? null,
            created_at: alert.created_at,
            resolved_at: alert.resolved_at ?? null,
            groups: alert.group ? [alert.group] : [],
            events: alert.event ? [alert.event] : [],
            alert_ids: [alert.id],
          });
        } else {
          const existing = batchMap.get(batchId)!;
          // Add group if not already present
          if (alert.group && !existing.groups.some(g => g.id === alert.group!.id)) {
            existing.groups.push(alert.group);
          }
          // Add event if not already present
          if (alert.event && !existing.events.some(e => e.id === alert.event!.id)) {
            existing.events.push(alert.event);
          }
          // Add alert ID
          existing.alert_ids.push(alert.id);
        }
      });
      
      setAlerts(Array.from(batchMap.values()));
    } catch (error) {
      console.error('Failed to load alerts:', error);
      toast({
        title: 'Error',
        description: 'Failed to load your alerts',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (alertId: string) => {
    try {
      setResolvingIds((prev) => new Set(prev).add(alertId));
      await safetyService.resolveAlert(alertId);
      
      toast({
        title: 'Alert resolved',
        description: 'The alert has been marked as resolved',
      });
      
      // Reload alerts to update the list
      await loadAlerts();
      
      // Dispatch custom event to notify other components (like Navbar)
      window.dispatchEvent(new CustomEvent('alert-resolved', { detail: { alertId } }));
    } catch (error: any) {
      console.error('Failed to resolve alert:', error);
      toast({
        title: 'Error',
        description: extractErrorMessage(error),
        variant: 'destructive',
      });
    } finally {
      setResolvingIds((prev) => {
        const next = new Set(prev);
        next.delete(alertId);
        return next;
      });
    }
  };

  const activeAlerts = alerts.filter((a) => !a.resolved_at);
  const displayAlerts = showResolved ? alerts : activeAlerts;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Your Safety Alerts
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant={activeAlerts.length > 0 ? 'destructive' : 'secondary'}>
              {activeAlerts.length} Active
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowResolved(!showResolved)}
            >
              {showResolved ? 'Hide Resolved' : 'Show All'}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        ) : displayAlerts.length === 0 ? (
          <Alert>
            <AlertDescription className="text-center py-4">
              {showResolved
                ? 'No alerts found'
                : 'No active alerts. You can send safety alerts during active events.'}
            </AlertDescription>
          </Alert>
        ) : (
          <div className="space-y-3">
            {displayAlerts.map((alert) => {
              const config = ALERT_TYPE_CONFIG[alert.alert_type];
              const Icon = config.icon;
              const isResolving = resolvingIds.has(alert.id);

              return (
                <div
                  key={alert.id}
                  className={`rounded-lg border p-4 ${
                    alert.resolved_at ? 'bg-muted/50' : config.bgColor
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${config.color}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`font-medium ${config.color}`}>
                            {config.label}
                          </span>
                          {alert.resolved_at && (
                            <Badge variant="outline" className="gap-1">
                              <CheckCircle className="w-3 h-3" />
                              Resolved
                            </Badge>
                          )}
                        </div>
                        {alert.message && (
                          <p className="text-sm text-muted-foreground mt-1">
                            {alert.message}
                          </p>
                        )}
                        
                        {/* Groups and Events info */}
                        {(alert.groups.length > 0 || alert.events.length > 0) && (
                          <div className="mt-2 space-y-1">
                            {alert.groups.length > 0 && (
                              <div className="flex items-center gap-1 flex-wrap text-xs text-muted-foreground">
                                <Users className="w-3 h-3 flex-shrink-0" />
                                <span>
                                  {alert.groups.map((g, i) => (
                                    <span key={g.id}>
                                      {i > 0 && ', '}
                                      {g.name}
                                    </span>
                                  ))}
                                </span>
                              </div>
                            )}
                            {alert.events.length > 0 && (
                              <div className="flex items-center gap-1 flex-wrap text-xs">
                                {alert.events.map((event, i) => (
                                  <span key={event.id} className="flex items-center gap-1">
                                    {i > 0 && <span className="text-muted-foreground">•</span>}
                                    <Link
                                      to={`/events/${event.id}`}
                                      className="flex items-center gap-1 text-primary hover:underline"
                                    >
                                      {event.name}
                                      <ExternalLink className="w-3 h-3" />
                                    </Link>
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                        
                        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground flex-wrap">
                          <div className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatDistanceToNow(new Date(alert.created_at), {
                              addSuffix: true,
                            })}
                          </div>
                          {alert.latitude && alert.longitude && (
                            <div className="flex items-center gap-1">
                              <MapPin className="w-3 h-3" />
                              Location shared
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    {!alert.resolved_at && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleResolve(alert.id)}
                        disabled={isResolving}
                        className="flex-shrink-0"
                      >
                        {isResolving ? (
                          <>
                            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                            Resolving...
                          </>
                        ) : (
                          <>
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Mark Resolved
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
