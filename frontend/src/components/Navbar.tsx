import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, Calendar, User, LogOut, AlertTriangle } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { useAppStore } from '../stores/appStore';
import { useState, useRef, useEffect } from 'react';

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuthStore();
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

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/events', icon: Calendar, label: 'Events' },
    { path: '/profile', icon: User, label: 'Profile' },
  ];

  return (
    <>
      {/* Desktop Navbar - Top */}
      <nav className="hidden md:block bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2">
              <img src="/icon.png" alt="CrewUp logo" className="h-8 w-8 rounded-md" />
              <span className="text-2xl font-bold text-gray-900 hidden sm:inline">CrewUp</span>
            </Link>

            <div className="flex items-center gap-6">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                    isActive(item.path)
                      ? 'text-primary-600 bg-primary-50 font-semibold shadow-sm'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <item.icon className={`w-5 h-5 ${isActive(item.path) ? 'stroke-[2.5]' : ''}`} />
                  <span className="font-medium">{item.label}</span>
                </Link>
              ))}
              
              <button
                onMouseDown={handleAlertStart}
                onMouseUp={handleAlertEnd}
                onMouseLeave={handleAlertEnd}
                onTouchStart={handleAlertStart}
                onTouchEnd={handleAlertEnd}
                className={`relative flex items-center gap-2 px-4 py-2 rounded-lg transition-all overflow-hidden ${
                  isPartyMode
                    ? 'bg-red-500 text-white hover:bg-red-600 shadow-md'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <div 
                  className="absolute inset-0 bg-red-300 transition-all"
                  style={{ 
                    width: `${progress}%`,
                    opacity: isLongPressing ? 0.5 : 0
                  }}
                />
                <AlertTriangle className="w-5 h-5 relative z-10" />
                <span className="font-medium relative z-10">{isPartyMode ? 'Alert ON' : 'Hold 2s'}</span>
              </button>
              
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <LogOut className="w-5 h-5" />
                <span className="font-medium">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Bottom Tab Bar - iOS Style */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 z-50">
        <div className="flex items-center justify-around px-2 py-2 safe-area-inset-bottom">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center gap-1 px-4 py-2 rounded-xl transition-all ${
                isActive(item.path)
                  ? 'text-primary-600 bg-primary-50'
                  : 'text-gray-500'
              }`}
            >
              <item.icon className={`w-6 h-6 ${isActive(item.path) ? 'stroke-[2.5]' : ''} transition-transform`} />
              <span className={`text-xs ${isActive(item.path) ? 'font-semibold' : 'font-medium'}`}>{item.label}</span>
            </Link>
          ))}
          
          <button
            onTouchStart={handleAlertStart}
            onTouchEnd={handleAlertEnd}
            className={`relative flex flex-col items-center gap-1 px-4 py-2 rounded-xl transition-all overflow-hidden ${
              isPartyMode
                ? 'bg-red-500 text-white'
                : 'text-gray-500'
            }`}
          >
            <div 
              className="absolute inset-0 bg-red-300 transition-all"
              style={{ 
                height: `${progress}%`,
                bottom: 0,
                top: 'auto',
                opacity: isLongPressing ? 0.5 : 0
              }}
            />
            <AlertTriangle className="w-6 h-6 relative z-10" />
            <span className="text-xs font-medium relative z-10">Alert</span>
          </button>
        </div>
      </nav>
    </>
  );
}
