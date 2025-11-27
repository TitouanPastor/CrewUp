import { useState, useEffect, useCallback } from 'react';
import { safetyService, type SafetyAlert } from '@/services/safetyService';

/**
 * Hook to track user's active safety alerts
 * Returns the most recent unresolved alert (if any)
 */
export function useActiveAlert() {
  const [activeAlert, setActiveAlert] = useState<SafetyAlert | null>(null);
  const [loading, setLoading] = useState(true);

  const loadActiveAlert = useCallback(async () => {
    try {
      setLoading(true);
      const { alerts } = await safetyService.getMyAlerts({
        resolved: false,
        limit: 1,
      });
      
      // Get the most recent unresolved alert
      setActiveAlert(alerts.length > 0 ? alerts[0] : null);
    } catch (error) {
      console.error('Failed to load active alert:', error);
      setActiveAlert(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadActiveAlert();
  }, [loadActiveAlert]);

  return {
    activeAlert,
    loading,
    refresh: loadActiveAlert,
  };
}
