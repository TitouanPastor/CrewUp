import { Link, useLocation } from 'react-router-dom';
import { Home, Calendar, User, AlertTriangle, Moon, Sun, CheckCircle, Loader2 } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import SafetyAlertDialog from './SafetyAlertDialog';
import { useActiveAlert } from '@/hooks/useActiveAlert';
import { safetyService } from '@/services/safetyService';
import { useToast } from '@/hooks/use-toast';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export default function Navbar() {
  const location = useLocation();
  const { setTheme } = useTheme();
  const { toast } = useToast();
  const { activeAlert, loading: loadingAlert, refresh: refreshAlert } = useActiveAlert();
  
  const [isLongPressing, setIsLongPressing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showAlertDialog, setShowAlertDialog] = useState(false);
  const [hasActiveEvents, setHasActiveEvents] = useState(true); // Optimistic default
  const [isResolving, setIsResolving] = useState(false);
  const longPressTimer = useRef<number | null>(null);
  const progressInterval = useRef<number | null>(null);

  // Listen for alert-resolved events from other components
  useEffect(() => {
    const handleAlertResolvedEvent = () => {
      refreshAlert();
    };
    
    const handleAlertCreatedEvent = () => {
      refreshAlert();
    };
    
    window.addEventListener('alert-resolved', handleAlertResolvedEvent);
    window.addEventListener('alert-created', handleAlertCreatedEvent);
    
    return () => {
      window.removeEventListener('alert-resolved', handleAlertResolvedEvent);
      window.removeEventListener('alert-created', handleAlertCreatedEvent);
    };
  }, [refreshAlert]);

  const handleAlertStart = () => {
    setIsLongPressing(true);
    let currentProgress = 0;

    progressInterval.current = window.setInterval(() => {
      currentProgress += 5;
      setProgress(currentProgress);
    }, 100);

    longPressTimer.current = window.setTimeout(async () => {
      setIsLongPressing(false);
      setProgress(0);
      if (progressInterval.current) clearInterval(progressInterval.current);
      
      // If user has active alert: resolve it
      if (activeAlert) {
        try {
          setIsResolving(true);
          await safetyService.resolveAlert(activeAlert.id);
          toast({
            title: 'Alert resolved',
            description: 'Your safety alert has been marked as resolved',
          });
          await refreshAlert(); // Refresh alert status
        } catch (error: any) {
          console.error('Failed to resolve alert:', error);
          toast({
            title: 'Failed to resolve alert',
            description: error.response?.data?.detail || 'Please try again',
            variant: 'destructive',
          });
        } finally {
          setIsResolving(false);
        }
      } else {
        // No active alert: open dialog to create one
        setShowAlertDialog(true);
      }
    }, 2000);
  };

  const handleAlertEnd = () => {
    if (longPressTimer.current) clearTimeout(longPressTimer.current);
    if (progressInterval.current) clearInterval(progressInterval.current);
    setIsLongPressing(false);
    setProgress(0);
  };

  useEffect(() => {
    return () => {
      if (longPressTimer.current) clearTimeout(longPressTimer.current);
      if (progressInterval.current) clearInterval(progressInterval.current);
    };
  }, []);

  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/events', icon: Calendar, label: 'Events' },
    { path: '/profile', icon: User, label: 'Profile' },
  ];

  return (
    <nav className="hidden md:block fixed top-0 inset-x-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="relative">
              <img
                src="/icon_transparent.png"
                alt="CrewUp"
                className="h-9 w-9 rounded-xl transition-transform group-hover:scale-105"
              />
            </div>
            <span className="text-xl font-semibold text-foreground tracking-tight">CrewUp</span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-2">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2 px-4 h-9 rounded-lg transition-all font-medium text-sm ${isActive(item.path)
                  ? 'text-primary bg-primary/10'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                  }`}
              >
                <item.icon className="w-4 h-4" />
                <span>{item.label}</span>
              </Link>
            ))}

            {/* Alert Button */}
            <Button
              variant={activeAlert ? "destructive" : "outline"}
              size="sm"
              onMouseDown={hasActiveEvents && !isResolving ? handleAlertStart : undefined}
              onMouseUp={hasActiveEvents && !isResolving ? handleAlertEnd : undefined}
              onMouseLeave={hasActiveEvents && !isResolving ? handleAlertEnd : undefined}
              onTouchStart={hasActiveEvents && !isResolving ? handleAlertStart : undefined}
              onTouchEnd={hasActiveEvents && !isResolving ? handleAlertEnd : undefined}
              disabled={!hasActiveEvents || isResolving || loadingAlert}
              className="relative overflow-hidden ml-2"
            >
              <div
                className="absolute inset-0 bg-destructive/30 transition-all"
                style={{
                  width: `${progress}%`,
                  opacity: isLongPressing ? 1 : 0
                }}
              />
              {isResolving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 relative z-10 animate-spin" />
                  <span className="relative z-10">Resolving...</span>
                </>
              ) : activeAlert ? (
                <>
                  <CheckCircle className="w-4 h-4 mr-2 relative z-10" />
                  <span className="relative z-10">Hold to Resolve</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 mr-2 relative z-10" />
                  <span className="relative z-10">
                    {!hasActiveEvents ? 'No Active Events' : 'Hold 2s'}
                  </span>
                </>
              )}
            </Button>

            {/* Theme Toggle */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="ml-2">
                  <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                  <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                  <span className="sr-only">Toggle theme</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setTheme("light")}>
                  Light
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("dark")}>
                  Dark
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("system")}>
                  System
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {/* Safety Alert Dialog */}
      <SafetyAlertDialog
        open={showAlertDialog}
        onOpenChange={setShowAlertDialog}
        onActiveEventsChange={setHasActiveEvents}
        onAlertSent={refreshAlert} // Refresh active alert after sending
      />
    </nav>
  );
}
