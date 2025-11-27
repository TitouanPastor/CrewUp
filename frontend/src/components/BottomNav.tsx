import { Link, useLocation } from 'react-router-dom';
import { Home, Calendar, User, AlertTriangle } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import SafetyAlertDialog from './SafetyAlertDialog';

const navItems = [
  { path: '/', icon: Home, label: 'Home' },
  { path: '/events', icon: Calendar, label: 'Events' },
  { path: '/profile', icon: User, label: 'Profile' },
];

export default function BottomNav() {
  const location = useLocation();
  const [isLongPressing, setIsLongPressing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showAlertDialog, setShowAlertDialog] = useState(false);
  const [hasActiveEvents, setHasActiveEvents] = useState(true); // Optimistic default
  const longPressTimer = useRef<number | null>(null);
  const progressInterval = useRef<number | null>(null);

  const handleAlertStart = () => {
    setIsLongPressing(true);
    let currentProgress = 0;
    
    progressInterval.current = window.setInterval(() => {
      currentProgress += 5;
      setProgress(currentProgress);
    }, 100);

    longPressTimer.current = window.setTimeout(() => {
      // Open alert dialog after 2s
      setShowAlertDialog(true);
      setIsLongPressing(false);
      setProgress(0);
      if (progressInterval.current) clearInterval(progressInterval.current);
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

  return (
    <>
      {/* Mobile Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-t border-border">
        <div className="flex items-center justify-around h-16 px-2" style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}>
          {navItems.map(({ path, icon: Icon, label }) => {
            const isActive = location.pathname === path || 
                            (path !== '/' && location.pathname.startsWith(path));
            
            return (
              <Link
                key={path}
                to={path}
                className={`flex flex-col items-center justify-center flex-1 h-full gap-0.5 transition-colors ${
                  isActive
                    ? 'text-primary'
                    : 'text-muted-foreground'
                }`}
              >
                <Icon className="w-6 h-6" strokeWidth={isActive ? 2.5 : 2} />
                <span className="text-[11px] font-medium">{label}</span>
              </Link>
            );
          })}
          
          {/* Alert Button */}
          <button
            onTouchStart={hasActiveEvents ? handleAlertStart : undefined}
            onTouchEnd={hasActiveEvents ? handleAlertEnd : undefined}
            disabled={!hasActiveEvents}
            className={`relative flex flex-col items-center justify-center flex-1 h-full gap-0.5 transition-colors overflow-hidden ${
              !hasActiveEvents
                ? 'text-muted-foreground/40 cursor-not-allowed'
                : showAlertDialog
                ? 'text-destructive'
                : 'text-muted-foreground'
            }`}
          >
            <div 
              className="absolute inset-0 bg-destructive/20 transition-all"
              style={{ 
                height: `${progress}%`,
                bottom: 0,
                top: 'auto',
                opacity: isLongPressing ? 1 : 0
              }}
            />
            <AlertTriangle className="w-6 h-6 relative z-10" strokeWidth={showAlertDialog ? 2.5 : 2} />
            <span className="text-[11px] font-medium relative z-10">Alert</span>
          </button>
        </div>
      </nav>

      {/* Safety Alert Dialog */}
      <SafetyAlertDialog
        open={showAlertDialog}
        onOpenChange={setShowAlertDialog}
        onActiveEventsChange={setHasActiveEvents}
      />
    </>
  );
}
