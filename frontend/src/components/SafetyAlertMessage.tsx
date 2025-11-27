import { AlertTriangle, Heart, ShieldAlert, HelpCircle, MapPin, Clock } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import type { SafetyAlert } from '@/services/safetyService';

interface SafetyAlertMessageProps {
  alert: SafetyAlert;
  currentUserId?: string;
}

const ALERT_TYPE_CONFIG = {
  help: {
    icon: HelpCircle,
    label: 'Help Needed',
    color: 'orange',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/30',
    textColor: 'text-orange-600 dark:text-orange-400',
  },
  medical: {
    icon: Heart,
    label: 'Medical Emergency',
    color: 'red',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    textColor: 'text-red-600 dark:text-red-400',
  },
  harassment: {
    icon: ShieldAlert,
    label: 'Harassment/Safety',
    color: 'purple',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
    textColor: 'text-purple-600 dark:text-purple-400',
  },
  other: {
    icon: AlertTriangle,
    label: 'Emergency',
    color: 'yellow',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/30',
    textColor: 'text-yellow-600 dark:text-yellow-400',
  },
} as const;

export default function SafetyAlertMessage({
  alert,
  currentUserId,
}: SafetyAlertMessageProps) {
  const config = ALERT_TYPE_CONFIG[alert.alert_type];
  const Icon = config.icon;
  const isOwnAlert = currentUserId === alert.user_id;
  const isResolved = alert.resolved || !!alert.resolved_at;

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    
    if (isToday) {
      return 'Today';
    }
    
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    }
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const handleMapClick = () => {
    if (alert.latitude && alert.longitude) {
      const url = `https://www.google.com/maps?q=${alert.latitude},${alert.longitude}`;
      window.open(url, '_blank');
    }
  };

  return (
    <Alert
      className={`relative ${config.bgColor} ${config.borderColor} border-2 ${
        isResolved ? 'opacity-60' : ''
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Alert Icon */}
        <div className={`p-2 rounded-full ${config.bgColor} mt-1`}>
          <Icon className={`w-5 h-5 ${config.textColor}`} />
        </div>

        {/* Alert Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between gap-2 mb-2">
            <div>
              <div className={`font-bold text-sm ${config.textColor}`}>
                {config.label}
              </div>
              <div className="text-xs text-muted-foreground">
                {isOwnAlert ? 'You' : (alert.user_name || 'Someone')} • {formatDate(alert.created_at)} at{' '}
                {formatTime(alert.created_at)}
              </div>
            </div>
            {isResolved && (
              <div className="text-xs font-medium text-green-600 dark:text-green-400 bg-green-500/10 px-2 py-1 rounded">
                Resolved
              </div>
            )}
          </div>

          {/* Message */}
          {alert.message && (
            <AlertDescription className="text-sm mb-2 text-foreground">
              {alert.message}
            </AlertDescription>
          )}

          {/* Location */}
          {alert.latitude && alert.longitude && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleMapClick}
              className={`h-auto px-2 py-1 ${config.textColor} hover:${config.bgColor}`}
            >
              <MapPin className="w-4 h-4 mr-1" />
              <span className="text-xs">View location on map</span>
            </Button>
          )}

          {/* Resolved timestamp */}
          {isResolved && alert.resolved_at && (
            <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="w-3 h-3" />
              Resolved at {formatTime(alert.resolved_at)}
            </div>
          )}
        </div>
      </div>
    </Alert>
  );
}
