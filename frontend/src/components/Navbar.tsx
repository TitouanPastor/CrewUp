import { Link, useLocation } from 'react-router-dom';
import { Home, Calendar, User, AlertTriangle, Moon, Sun } from 'lucide-react';
import { useAppStore } from '../stores/appStore';
import { useState, useRef, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export default function Navbar() {
  const location = useLocation();
  const { setTheme } = useTheme();
  const { isPartyMode, togglePartyMode } = useAppStore();
  const [isLongPressing, setIsLongPressing] = useState(false);
  const [progress, setProgress] = useState(0);
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
      togglePartyMode();
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

  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/events', icon: Calendar, label: 'Events' },
    { path: '/profile', icon: User, label: 'Profile' },
  ];

  return (
    <nav className="hidden md:block bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border sticky top-0 z-50">
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
                className={`flex items-center gap-2 px-4 h-9 rounded-lg transition-all font-medium text-sm ${
                  isActive(item.path)
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
              variant={isPartyMode ? "destructive" : "outline"}
              size="sm"
              onMouseDown={handleAlertStart}
              onMouseUp={handleAlertEnd}
              onMouseLeave={handleAlertEnd}
              onTouchStart={handleAlertStart}
              onTouchEnd={handleAlertEnd}
              className="relative overflow-hidden ml-2"
            >
              <div 
                className="absolute inset-0 bg-destructive/30 transition-all"
                style={{ 
                  width: `${progress}%`,
                  opacity: isLongPressing ? 1 : 0
                }}
              />
              <AlertTriangle className="w-4 h-4 mr-2 relative z-10" />
              <span className="relative z-10">{isPartyMode ? 'Alert ON' : 'Hold 2s'}</span>
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
    </nav>
  );
}
