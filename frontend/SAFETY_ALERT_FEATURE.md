# Safety Alert System - Frontend Implementation

## Overview
The Safety Alert System allows users to send emergency alerts to their active event groups with a simple long-press interaction (2 seconds). This MVP implementation provides a quick way to signal for help during events.

## Features

### 1. **Long Press to Alert**
- Desktop: Hold the "Hold 2s" button in the navbar for 2 seconds
- Mobile: Long press the "Alert" button in the bottom navigation for 2 seconds
- Visual feedback: Progress bar fills during the press

### 2. **Smart Alert Dialog**
- **Auto-send**: Automatically sends alert after 5 seconds with default settings
- **Customization**: Click anywhere to customize before sending
- **Alert Types**:
  - 🆘 Help Needed (general assistance)
  - ❤️ Medical Emergency
  - 🛡️ Harassment/Safety
  - ⚠️ Other Emergency

### 3. **Automatic Context Detection**
- Detects all active events where user has RSVP'd "going"
- Filters events currently happening (between event_start and event_end)
- Shows all groups user belongs to in those events
- Pre-selects all groups by default

### 4. **Location Sharing**
- Automatically captures GPS location if permission granted
- Falls back gracefully if location unavailable
- Users can view alert location on map

### 5. **Group Chat Integration**
- Alerts appear prominently in group chat with red/orange styling
- Shows alert type, message, time, and location link
- Any group member can mark alert as "Resolved"
- Resolved alerts are dimmed but remain visible

## Components

### `SafetyAlertDialog.tsx`
Main alert configuration dialog with:
- Alert type selection (4 types)
- Optional message input
- Group selection (multi-select with all selected by default)
- Auto-send countdown (5s) or manual send
- Location capture

### `SafetyAlertMessage.tsx`
Displays safety alerts in group chat:
- Color-coded by alert type
- Shows user, timestamp, message
- Clickable location link
- Resolve button
- Resolved state indication

### `SafetyAlertService.ts`
API service for:
- `createAlert()` - Send alert to group
- `listAlerts()` - Get alerts for group/event
- `resolveAlert()` - Mark alert as resolved
- `getCurrentLocation()` - Get user's GPS coordinates

## User Flow

1. **Trigger**: User holds alert button for 2 seconds
2. **Dialog Opens**: Shows customization options
3. **Auto-send Timer**: 5 second countdown starts
4. **Two Paths**:
   - **Path A (Emergency)**: User doesn't interact → Alert auto-sends with defaults
   - **Path B (Customization)**: User clicks anything → Timer stops, manual send required
5. **Sending**: Alert sent to all selected groups with location
6. **Display**: Alert appears in group chats immediately
7. **Resolution**: Any member can mark as resolved

## Default Behavior (Emergency Mode)

When user is in actual emergency and can't customize:
- Alert Type: "Help Needed"
- Message: "Emergency - need help!"
- Groups: All active event groups (pre-selected)
- Location: Automatically captured if available
- Sends after 5 seconds

## API Endpoints

```typescript
POST /api/v1/safety/alert
Body: {
  event_id: string,
  group_id: string,
  alert_type: 'help' | 'medical' | 'harassment' | 'other',
  message?: string,
  latitude?: number,
  longitude?: number
}

GET /api/v1/safety/alerts?group_id={id}
Response: {
  alerts: SafetyAlert[],
  total: number
}

PUT /api/v1/safety/alerts/{id}/resolve
Response: SafetyAlert
```

## WebSocket Integration

Alerts are broadcast to all group members via WebSocket:
```typescript
{
  type: 'safety_alert',
  alert_data: SafetyAlert
}
```

## Future Enhancements (Not in MVP)

- Push notifications for alerts
- Sound/vibration alerts
- Alert history page
- Alert analytics for event organizers
- Geofencing (auto-alert if user leaves event area)
- SOS contacts outside the app
- Integration with local emergency services
- Voice-activated alerts
- Shake-to-alert gesture
- Silent alert mode (no notification to attacker)

## Testing Considerations

- Test with/without location permission
- Test auto-send timer (should send at 5s)
- Test manual customization (timer should stop)
- Test with multiple active events
- Test with no active events
- Test resolve functionality
- Test real-time updates via WebSocket

## Accessibility

- Keyboard navigation support
- Screen reader friendly
- High contrast alert colors
- Clear visual feedback for long-press
- Text alternatives for icons

## Browser Compatibility

- Geolocation API (falls back gracefully)
- Touch events for mobile long-press
- Mouse events for desktop long-press
- WebSocket for real-time updates
